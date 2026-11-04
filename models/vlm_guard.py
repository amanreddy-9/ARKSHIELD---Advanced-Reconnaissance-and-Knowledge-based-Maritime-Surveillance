"""Process-shared, non-sleeping Groq admission control. Never logs request content."""
import hashlib
import json
import logging
import os
import re
import threading
import time
from collections import Counter, OrderedDict
from email.utils import parsedate_to_datetime

log = logging.getLogger(__name__)

class RequestGuard:
    _guards = {}
    _registry_lock = threading.Lock()

    @classmethod
    def shared(cls, model):
        # Organization limits can affect all models/keys; share conservatively.
        with cls._registry_lock:
            return cls._guards.setdefault('organization', cls())

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.lock = threading.RLock()
        self.cooldown_until = 0.0
        self.next_request = 0.0
        self.failures = 0
        self.stats = Counter()
        self.cache = OrderedDict()
        self.last_source = 'unavailable'
        self.day_started = clock()
        self.spent = 0
        self.minimum_interval = max(0, float(os.getenv('GROQ_MIN_INTERVAL_SECONDS', '10')))
        self.daily_budget = max(0, int(os.getenv('GROQ_LOCAL_TOKEN_BUDGET', '180000')))
        self.reserve = max(1, int(os.getenv('GROQ_REQUEST_TOKEN_RESERVE', '3000')))
        self.cache_ttl = max(0, float(os.getenv('GROQ_CACHE_TTL_SECONDS', '3600')))

    def track_cache_hit(self):
        with self.lock:
            self.stats["track_cache_hits"] += 1

    def snapshot(self, enabled=True):
        with self.lock:
            remaining = max(0, self.cooldown_until-self.clock(), self.next_request-self.clock())
            return {'status': 'disabled' if not enabled else ('unavailable' if remaining or self.spent+self.reserve>self.daily_budget else 'ready'),
                    'retry_after_seconds': round(remaining, 2), 'counters': dict(self.stats),
                    'local_budget_used': self.spent, 'local_budget_limit': self.daily_budget}

    def _retry_delay(self, exc):
        headers = getattr(getattr(exc, 'response', None), 'headers', {}) or {}
        raw = headers.get('retry-after')
        if raw:
            try: return max(0, float(raw))
            except ValueError:
                try: return max(0, parsedate_to_datetime(raw).timestamp()-time.time())
                except (ValueError, TypeError): pass
        body = getattr(exc, 'body', None)
        message = str(body if body else exc)  # inspected only; never logged
        match = re.search(r'try again in\s*(?:(\d+(?:\.\d+)?)h)?(?:(\d+(?:\.\d+)?)m)?(?:(\d+(?:\.\d+)?)s)?', message, re.I)
        if match and any(match.groups()):
            return sum(float(x or 0)*factor for x, factor in zip(match.groups(), (3600,60,1)))
        return min(300, 5*2**min(self.failures-1,6))

    def request(self, client, kwargs):
        key = hashlib.sha256(json.dumps(kwargs, sort_keys=True).encode()).hexdigest()
        with self.lock:  # serialize admission and completion; no duplicate in-flight requests
            now = self.clock()
            cached = self.cache.get(key)
            if cached and now-cached[0] < self.cache_ttl:
                self.stats['cache_hits'] += 1
                self.last_source = 'cached'
                log.info('groq event=cache_hit counters=%s', dict(self.stats))
                return cached[1]
            if now-self.day_started >= 86400:
                self.day_started, self.spent = now, 0
            if now < max(self.cooldown_until,self.next_request) or self.spent+self.reserve>self.daily_budget:
                self.stats['suppressed'] += 1
                self.last_source = 'unavailable'
                raise RuntimeError('VLM request deferred')
            self.next_request = now+self.minimum_interval
            self.spent += self.reserve
            self.stats['requests'] += 1
            try:
                result = client.chat.completions.create(**kwargs)
            except Exception as exc:
                self.last_source = 'unavailable'
                self.failures += 1
                limited = getattr(exc, 'status_code', None) == 429
                self.stats['rate_limit_events' if limited else 'errors'] += 1
                delay = self._retry_delay(exc) if limited else min(300,5*2**min(self.failures-1,6))
                self.cooldown_until = self.clock()+max(1, delay)
                log.warning('groq event=%s cooldown_seconds=%.2f counters=%s', 'rate_limit' if limited else 'error', delay, dict(self.stats))
                raise RuntimeError('VLM temporarily unavailable') from None
            self.failures = 0
            usage = getattr(result, 'usage', None)
            total = getattr(usage, 'total_tokens', None)
            if total is not None:
                self.stats['tokens'] += total
                self.spent += total-self.reserve
                self.stats['prompt_tokens'] += getattr(usage,'prompt_tokens',0) or 0
                self.stats['completion_tokens'] += getattr(usage,'completion_tokens',0) or 0
            else:
                self.stats['usage_unknown_requests'] += 1
            self.stats['successes'] += 1
            self.cache[key] = (self.clock(), result)
            self.cache.move_to_end(key)
            while len(self.cache)>128: self.cache.popitem(last=False)
            self.last_source = 'fresh'
            log.info('groq event=success counters=%s', dict(self.stats))
            return result
