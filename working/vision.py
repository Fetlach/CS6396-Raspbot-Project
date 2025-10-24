# OpenCV-based color counting and centroid locating utilities.
# Camera handling can be via cv2.VideoCapture on Raspberry Pi.

import cv2
import numpy as np
from typing import Dict, Tuple, Optional
import config

ColorCounts = Dict[str, int]
Point2D = Tuple[int, int]

def count_colors_and_masks(frame_bgr):
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    counts: ColorCounts = {}
    masks = {}
    for color, ranges in config.HSV_THRESHOLDS.items():
        mask_total = None
        for (h1,s1,v1,h2,s2,v2) in ranges:
            lower = np.array([h1, s1, v1]); upper = np.array([h2, s2, v2])
            mask = cv2.inRange(hsv, lower, upper)
            mask_total = mask if mask_total is None else cv2.bitwise_or(mask_total, mask)
        # Morph to clean noise
        kernel = np.ones((5,5), np.uint8)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_DILATE, kernel)
        masks[color] = mask_total
        counts[color] = int(np.count_nonzero(mask_total))
    return counts, masks

def largest_color(counts: ColorCounts):
    if not counts:
        return None
    color, mx = None, 0
    for c, v in counts.items():
        if v > mx:
            color, mx = c, v
    if color is None or mx < config.MIN_PIXELS_VISIBLE:
        return None
    return color

def centroid_from_mask(mask: np.ndarray):
    M = cv2.moments(mask)
    if M["m00"] == 0:
        return None
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    return (cx, cy)
