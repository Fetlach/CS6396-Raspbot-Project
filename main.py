
def classifyColor(r, g, b, shareThreshold) -> int:
    # red = 1, green = 2, blue = 3, none = 0
    value = float(r) + float(g) + float(b)
    rshare = float(r) / float(value)
    gshare = float(g) / float(value)
    bshare = float(b) / float(value)
    if rshare > gshare and rshare > bshare and rshare > shareThreshold:
        return 1
    elif gshare > rshare and gshare > bshare and gshare > shareThreshold:
        return 2
    elif bshare > rshare and bshare > gshare and bshare > shareThreshold:
        return 3
    else:
        return 0

def colorCounter(image, imageDimX, imageDimY, shareThreshold) -> dict:
    # red = 1, green = 2, blue = 3, none = 0
    colorDict = {
        0: 0,
        1: 0,
        2: 0,
        3: 0
    }

    for i in range(imageDimY):
        for j in range(imageDimX):
            pixel = image[i, j]
            colorDict[classifyColor(pixel[0], pixel[1], pixel[2], shareThreshold)] += 1

    return colorDict

