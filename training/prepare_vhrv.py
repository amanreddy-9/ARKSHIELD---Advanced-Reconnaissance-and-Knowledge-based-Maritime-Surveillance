import argparse
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--source",required=True)
p.add_argument("--output",required=True)
a=p.parse_args()
print("Source:",Path(a.source).resolve())
print("Output:",Path(a.output).resolve())
print("Inspect the downloaded VHRV annotations and convert them to Ultralytics OBB format.")
print("This helper intentionally does not guess an annotation format.")
