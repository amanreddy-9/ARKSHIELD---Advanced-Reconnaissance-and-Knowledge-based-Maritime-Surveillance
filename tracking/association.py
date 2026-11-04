"""
tracking/association.py
Data Association and Matching Utilities for Maritime Vessel Tracking.

Combines:
1. Bounding-Box Intersection over Union (IoU)
2. Normalized Euclidean centroid distance
3. Box dimension and aspect-ratio geometric similarity
4. Motion vector direction consistency
5. Sub-part / deck-fitting suppression
"""
import math
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

try:
    from scipy.optimize import linear_sum_assignment
except ImportError:
    linear_sum_assignment = None


def bbox_iou(box1: List[float], box2: List[float]) -> float:
    """
    Computes Intersection over Union (IoU) between two horizontal bounding boxes.
    Boxes are in format [x1, y1, x2, y2].
    """
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])

    inter_w = max(0.0, xB - xA)
    inter_h = max(0.0, yB - yA)
    inter_area = inter_w * inter_h

    box1_area = max(0.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
    box2_area = max(0.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))

    union_area = box1_area + box2_area - inter_area
    if union_area <= 0.0:
        return 0.0
    return float(inter_area / union_area)


def size_similarity(tw: float, th: float, dw: float, dh: float) -> float:
    """
    Computes geometric dimension and aspect-ratio similarity in range [0.0, 1.0].
    """
    tw, th = max(1.0, float(tw)), max(1.0, float(th))
    dw, dh = max(1.0, float(dw)), max(1.0, float(dh))

    w_ratio = min(tw, dw) / max(tw, dw)
    h_ratio = min(th, dh) / max(th, dh)

    tar = tw / th
    dar = dw / dh
    ar_ratio = min(tar, dar) / max(tar, dar)

    return float(0.5 * (w_ratio + h_ratio) * ar_ratio)


def measurement_for_track(detection,track):
    """Weak anisotropically truncated boxes measure only their reliable axes.
    This is not a fabricated full box: the missing dimensions are unobserved.
    Full/zoomed boxes retain all four measurements.
    """
    box=detection.get('bbox')
    if box is not None:
        z=np.array([(box[0]+box[2])/2,(box[1]+box[3])/2,max(1.,box[2]-box[0]),max(1.,box[3]-box[1])])
    else:z=np.array([detection.get('cx',track.cx),detection.get('cy',track.cy),detection.get('w',track.w),detection.get('h',track.h)],dtype=float)
    mask=np.ones(4,dtype=bool)
    if getattr(track,'time_aware',False) and hasattr(track,'reference_size'):
        ratios=z[2:]/np.maximum(track.reference_size,1.)
        conf=float(detection.get('confidence',detection.get('conf',1.)))
        if box is not None and bbox_iou(box,track.bbox)>.30:
            tb=track.bbox
            intersection=max(0.,min(box[2],tb[2])-max(box[0],tb[0]))*max(0.,min(box[3],tb[3])-max(box[1],tb[1]))
            containment=intersection/max(1.,z[2]*z[3])
            # Confidence in a visible hull fragment does not make its missing
            # extent a reliable size measurement. Require containment and an
            # otherwise comparable axis; isotropic zoom keeps full updates.
            if containment>=.60:
                if ratios[1]<.85 and .80<ratios[0]<1.25:mask[[1,3]]=False
                elif ratios[0]<.85 and .80<ratios[1]<1.25:mask[[0,2]]=False
    return z,mask


def compute_association_cost(detection: Dict[str, Any], track: Any, mahalanobis_gate=None, diagnostics=None) -> Optional[float]:
    """
    Computes a multi-feature association cost between a predicted track and a detection.
    Returns:
        float cost in range [0.0, 1.0] (lower is better), or None if physically infeasible.
    """
    detail = diagnostics if diagnostics is not None else {}
    det_box = detection.get("bbox")
    if det_box is None:
        dw = float(detection.get("w", 0.0))
        dh = float(detection.get("h", 0.0))
        det_cx = float(detection.get("cx", 0.0))
        det_cy = float(detection.get("cy", 0.0))
        det_w = dw
        det_h = dh
        det_box = [
            det_cx - dw / 2.0,
            det_cy - dh / 2.0,
            det_cx + dw / 2.0,
            det_cy + dh / 2.0,
        ]
    else:
        det_cx = float(detection.get("cx", (det_box[0] + det_box[2]) / 2.0))
        det_cy = float(detection.get("cy", (det_box[1] + det_box[3]) / 2.0))
        det_w = float(detection.get("w", det_box[2] - det_box[0]))
        det_h = float(detection.get("h", det_box[3] - det_box[1]))

    track_box = track.bbox
    iou = bbox_iou(track_box, det_box)

    dist = math.hypot(det_cx - track.cx, det_cy - track.cy)
    diag = max(math.hypot(track.w, track.h), 30.0)
    sim = size_similarity(track.w, track.h, det_w, det_h)

    if mahalanobis_gate is not None:
        z,measurement_mask=measurement_for_track(detection,track)
        effective_gate=(13.8155 if mahalanobis_gate>14 else 9.2103) if measurement_mask.sum()==2 else mahalanobis_gate
        residual,covariance,_=track.kf.innovation(z, detection.get("confidence", detection.get("conf", 1.0)),measurement_mask)
        if measurement_mask.sum()==2:
            trusted_size=np.where(measurement_mask[2:],z[2:],np.array([track.w,track.h]))
            sim=size_similarity(track.w,track.h,*trusted_size)
        try:
            d2=float((residual.T@np.linalg.solve(covariance,residual)).item())
        except np.linalg.LinAlgError:
            detail.update(reason="singular_innovation_covariance")
            return None
        detail.update(mahalanobis_squared=d2,statistical_gate=effective_gate,size_similarity=sim,measurement_components=np.flatnonzero(measurement_mask).tolist())
        if not np.isfinite(d2) or d2>effective_gate:
            detail.update(reason="mahalanobis_gate");return None
        if sim<.25:
            detail.update(reason="shape_gate");return None

    # Adaptive search radius expands dynamically when track was coasted through occlusion
    if mahalanobis_gate is None:
        max_dist = max(120.0, 1.8 * diag) + track.missed_frames * 12.0
    else:
        uncertainty=float(np.sqrt(max(track.kf.P[0,0],track.kf.P[1,1])))
        max_dist=max(80.,1.2*diag)+min(150.,3*uncertainty)

    if dist > max_dist and iou < 0.05:
        detail.update(reason="centroid_distance_gate",distance=dist,max_distance=max_dist)
        return None

    # Cost components
    iou_cost = 1.0 - iou
    norm_dist = min(dist / max_dist, 1.0)
    size_cost = 1.0 - sim

    # Direction consistency
    motion_cost = 0.0
    v_mag = math.hypot(track.vx, track.vy)
    if v_mag > 2.0:
        pred_dx = det_cx - (track.cx - track.vx * (track.dt if getattr(track,"time_aware",False) else 1.))
        pred_dy = det_cy - (track.cy - track.vy * (track.dt if getattr(track,"time_aware",False) else 1.))
        p_mag = math.hypot(pred_dx, pred_dy)
        if p_mag > 0.0:
            cos_angle = (track.vx * pred_dx + track.vy * pred_dy) / (v_mag * p_mag)
            motion_cost = max(0.0, (1.0 - cos_angle) / 2.0)

    # Weighted affinity combination
    if iou >= 0.20:
        # Spatial overlap dominates for proximate vessels
        cost = 0.60 * iou_cost + 0.20 * norm_dist + 0.20 * size_cost
    else:
        # Proximity and shape consistency dominate during maneuvering or coasting
        cost = 0.35 * iou_cost + 0.35 * norm_dist + 0.20 * size_cost + 0.10 * motion_cost

    if mahalanobis_gate is not None:
        conf=float(detection.get("confidence",detection.get("conf",1.0)))
        cost=.85*cost+.10*min(d2/effective_gate,1.)+.05*(1.-np.clip(conf,0,1))
    return float(cost)


def associate_detections_to_tracks(
    detections: List[Dict[str, Any]],
    track_ids: List[int],
    tracks_dict: Dict[int, Any],
    used_detections: Set[int],
    max_cost: float = 0.85,
    mahalanobis_gate=None,
    reject_ambiguous=False,
    diagnostics=None,
) -> List[Tuple[int, int]]:
    """
    Perform 1-to-1 minimum cost matching between candidate detections and active tracks.
    Uses Hungarian algorithm with greedy fallback.

    Returns:
        List of (detection_index, track_id) tuples.
    """
    candidate_dets = [
        (idx, det) for idx, det in enumerate(detections)
        if idx not in used_detections
    ]
    if linear_sum_assignment is None:
        raise RuntimeError("Three-stage Hungarian tracking requires scipy. Install project requirements.")
    if not candidate_dets or not track_ids:
        return []

    # Build cost matrix
    num_dets = len(candidate_dets)
    num_tracks = len(track_ids)
    cost_matrix = np.full((num_dets, num_tracks), 1e5, dtype=np.float64)

    for i, (orig_det_idx, det) in enumerate(candidate_dets):
        for j, t_id in enumerate(track_ids):
            track = tracks_dict.get(t_id)
            if track is None:
                continue
            detail={}
            cost = compute_association_cost(det, track, mahalanobis_gate, detail)
            if diagnostics is not None and (cost is None or cost>max_cost):
                diagnostics.append({"event":"association_rejected","track_id":t_id,
                                    "detection_index":orig_det_idx,"reason":detail.get("reason","matching_cost_limit"),**detail})
            if cost is not None and cost <= max_cost:
                cost_matrix[i, j] = cost

    matches = []
    matched_dets = set()
    matched_tracks = set()

    if linear_sum_assignment is not None:
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        for r, c in zip(row_ind, col_ind):
            if cost_matrix[r, c] <= max_cost:
                if reject_ambiguous:
                    row_others=np.delete(cost_matrix[r],c)
                    col_others=np.delete(cost_matrix[:,c],r)
                    if ((row_others.size and row_others.min()<cost_matrix[r,c]+.04) or
                        (col_others.size and col_others.min()<cost_matrix[r,c]+.04)):
                        if diagnostics is not None: diagnostics.append({"event":"association_rejected","reason":"ambiguous_recovery","track_id":track_ids[c]})
                        continue
                orig_det_idx = candidate_dets[r][0]
                t_id = track_ids[c]
                matches.append((orig_det_idx, t_id))
                matched_dets.add(orig_det_idx)
                matched_tracks.add(t_id)
    else:
        # Greedy fallback
        candidates = []
        for i, (orig_det_idx, _) in enumerate(candidate_dets):
            for j, t_id in enumerate(track_ids):
                c = cost_matrix[i, j]
                if c <= max_cost:
                    candidates.append((c, orig_det_idx, t_id))
        candidates.sort(key=lambda x: x[0])
        for c, orig_det_idx, t_id in candidates:
            if orig_det_idx in matched_dets or t_id in matched_tracks:
                continue
            matched_dets.add(orig_det_idx)
            matched_tracks.add(t_id)
            matches.append((orig_det_idx, t_id))

    return matches


def is_subpart_detection(
    det: Dict[str, Any],
    active_matched_tracks: List[Any],
    iou_thresh: float = 0.25,
) -> bool:
    """
    Check if a detection corresponds to an internal deck sliver or structural sub-part
    of an already tracked vessel.
    """
    dw = float(det.get("w", 0.0))
    dh = float(det.get("h", 0.0))
    det_cx = float(det.get("cx", 0.0))
    det_cy = float(det.get("cy", 0.0))
    det_box = det.get("bbox")
    if det_box is None: det_box = [
        det_cx - dw / 2.0,
        det_cy - dh / 2.0,
        det_cx + dw / 2.0,
        det_cy + dh / 2.0,
    ]

    det_cx=(det_box[0]+det_box[2])/2
    det_cy=(det_box[1]+det_box[3])/2
    det_area = max(1.0, (det_box[2] - det_box[0]) * (det_box[3] - det_box[1]))

    for track in active_matched_tracks:
        tb = track.bbox
        iou_val = bbox_iou(tb, det_box)

        # Intersection area
        xA = max(tb[0], det_box[0])
        yA = max(tb[1], det_box[1])
        xB = min(tb[2], det_box[2])
        yB = min(tb[3], det_box[3])
        inter_area = max(0.0, xB - xA) * max(0.0, yB - yA)
        containment = inter_area / det_area

        center_inside = (tb[0] <= det_cx <= tb[2]) and (tb[1] <= det_cy <= tb[3])
        track_area=max(1.,(tb[2]-tb[0])*(tb[3]-tb[1]))
        # Overlap alone must not suppress a second full-size adjacent vessel.
        if center_inside and det_area < .65*track_area and containment >= .60:
            return True

    return False


def same_vessel_footprint(box, other, minimum_iou=.45):
    """Conservative duplicate birth guard; adjacent centers remain distinct."""
    w,h=max(1.,box[2]-box[0]),max(1.,box[3]-box[1])
    ow,oh=max(1.,other[2]-other[0]),max(1.,other[3]-other[1])
    dx=abs((box[0]+box[2]-other[0]-other[2])/2)
    dy=abs((box[1]+box[3]-other[1]-other[3])/2)
    return (bbox_iou(box,other)>=minimum_iou and
            dx/min(w,ow)<=.30 and dy/min(h,oh)<=.30 and
            min(w,ow)/max(w,ow)>=.55 and min(h,oh)/max(h,oh)>=.55)
