import torch


def nms(boxes, scores, iou_threshold=0.5, max_candidates=3000):
    """
    Memory-efficient Non-Maximum Suppression.

    boxes:  [N, 4] -> x1, y1, x2, y2
    scores: [N]
    """

    if boxes.numel() == 0:
        return torch.empty(
            (0,),
            dtype=torch.long,
            device=boxes.device
        )

    # Keep only the highest-confidence candidates.
    if boxes.shape[0] > max_candidates:
        top_scores, top_indices = torch.topk(
            scores,
            max_candidates
        )
        boxes = boxes[top_indices]
        scores = top_scores

    order = scores.argsort(descending=True)
    keep = []

    while order.numel() > 0:

        current = order[0]
        keep.append(current)

        if order.numel() == 1:
            break

        current_box = boxes[current]

        remaining_indices = order[1:]
        remaining_boxes = boxes[remaining_indices]

        x1 = torch.maximum(
            current_box[0],
            remaining_boxes[:, 0]
        )

        y1 = torch.maximum(
            current_box[1],
            remaining_boxes[:, 1]
        )

        x2 = torch.minimum(
            current_box[2],
            remaining_boxes[:, 2]
        )

        y2 = torch.minimum(
            current_box[3],
            remaining_boxes[:, 3]
        )

        intersection = (
            (x2 - x1).clamp(min=0)
            *
            (y2 - y1).clamp(min=0)
        )

        current_area = (
            (current_box[2] - current_box[0]).clamp(min=0)
            *
            (current_box[3] - current_box[1]).clamp(min=0)
        )

        remaining_area = (
            (remaining_boxes[:, 2] - remaining_boxes[:, 0]).clamp(min=0)
            *
            (remaining_boxes[:, 3] - remaining_boxes[:, 1]).clamp(min=0)
        )

        union = (
            current_area
            + remaining_area
            - intersection
        )

        iou = intersection / union.clamp(min=1e-7)

        order = remaining_indices[iou <= iou_threshold]

    return torch.stack(keep)


if __name__ == "__main__":

    boxes = torch.tensor([
        [10., 10., 100., 100.],
        [15., 15., 95., 95.],
        [200., 200., 300., 300.]
    ])

    scores = torch.tensor([
        0.90,
        0.80,
        0.70
    ])

    keep = nms(
        boxes,
        scores,
        iou_threshold=0.5
    )

    print("NMS test successful")
    print("Input boxes:", len(boxes))
    print("Boxes kept:", len(keep))
    print("Kept indices:", keep.tolist())
