import threading
import time
from collections import deque
import RotatoSettings

class task:
    def __task__(self, name, quantTime):
        self.name = name
        self.quantTime = quantTime
        self.remainingTime = quantTime

class redTask(task):
    pass 
class greenTask(task):
    pass 
class blueTask(task):
    pass 

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

def ColorCounter(image, imageDimX, imageDimY, shareThreshold) -> dict:
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

def ColorLocator(image, imageDimX, imageDimY, shareThreshold, color_counts):
    colorType = max(color_counts, key=color_counts.get)
    averageX = 0.0
    averageY = 0.0
    numPoint = 0.0

    for i in range(imageDimY):
        for j in range(imageDimX):
            pixel = image[i, j]
            if classifyColor(pixel[0], pixel[1], pixel[2], shareThreshold) is colorType:
                numPoint += 1
                averageX += j
                averageY += i

    averageX /= numPoint
    averageY /= numPoint

    return tuple(averageX, averageY)

def current_milli_time():
    return round(time.time() * 1000)

def main() :
    # --- Setup --- #
    currTime = 0.0
    lastTick = 0.0

    # -- update loop --- #
    taskQueue = deque(task)
    tasksInQueue = {} # dict to keep track of queued tasks
    while currTime < RotatoSettings.timeLimit:
        currTime = current_milli_time()

        # --- per-update functions --- #
        # read camera
        # threshold color

        # if color threshold achieved and task not in queue, insert task into queue; make sure to add bookkeeping to tasksInQueue
        # otherwise do nothing

        # --- Round-robin --- #
        while taskQueue:
            currTime
        # if no task currently executing, pop next task from the queue and execute
        # when time exceeds, move to next task (maybe reschedule task if it does not complete in time?)
        # if no tasks, do nothing

    # --- end --- #

    pass


if __name__ == "__main__":
    print("Starting program")
    main()
    print("Ending program")
