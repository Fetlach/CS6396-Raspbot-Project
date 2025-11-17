from vision import count_colors_and_masks, largest_color, centroid_from_mask

def ColorCounter(image, shareThreshold) -> dict:
    counts, masks = count_colors_and_masks(image)
    print(f"[ColorCounts] counts = {counts}")
    return counts, masks
    
    
def ColorLocator(color_counts, masks)->tuple:
    dom = largest_color(color_counts)
    if dom is None:
        print("[ColorLocator] No dominant color (idle).")
        return 0, (0.5,0.5)

    centroid = centroid_from_mask(masks[dom])
    if centroid is None:
        print("[ColorLocator] Dominant color but centroid not found -> idle.")
        return dom, (0.5,0.5)

    print(f"[ColorLocator] dominant = {dom}, centroid = {centroid}")
    return dom, centroid