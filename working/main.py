# external libraries
import threading
import cv2
from collections import deque
import simple_pid
from McLumk_Wheel_Sports import *# external libraries
import threading
import time
from PIDController import PIDController_Blue, PIDController_Green, PIDManager
from Task import task, redTask, blueTask, greenTask
import config
from robot import Raspbot
from vision import count_colors_and_masks, largest_color, centroid_from_mask
# our files
import RotatoSettings
from RobotState import blue_delta_value, green_delta_value
from Utils import current_milli_time
# allows for controlling input according to keyboard
debug = True


# how to use:
# - Set to a target delta (IE: position of the midpoint) with setNewPoint
#   - (internal PID is set to a zero position each time)
#   - This also enables the PID
# - call update every n seconds, use output to drive motors; will return false as second output when moving
#   - PID likes fixed timestepping, so need to reset if delayed to much
# - once the PID converges for n updates it will return true as the second output of the update function
#   - It will automatically disable itself once this happens





def StartupAction(bot: Raspbot):
    print("[StartupAction] Spinning to indicate init OK...")
    # total_deg = config.SPIN_DEG_TARGET
    # bot.spin_approx_degrees(total_deg, config.SPIN_POWER, config.SPIN_DEG_PER_SEC)
    # bot.sleep(config.SPIN_EXTRA_SAFETY)
    # bot.stop()
    duration = 2.8
    speed = 100
    try:
        rotate_left(speed)
        time.sleep(duration)
        stop_robot()
        time.sleep(1)
        # rotate_right(speed)
        # time.sleep(duration)
        # stop_robot()
        # time.sleep(1)

    except KeyboardInterrupt:
        # 当用户按下停止时，停止小车运动功能 When the user presses the stop button, the car stops moving.
            stop_robot()
            print("off.")
    print("[StartupAction] Complete. Entering round-robin loop.")

class imageState:
    pass

def classifyColor(r, g, b, shareThreshold) -> int:
    # red = 1, green = 2, blue = 3, none = 0
    value = float(r) + float(g) + float(b)
    if value <= 0.05:
        return 0
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

def ColorCounter(image, shareThreshold) -> dict:
    # rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # height, width, channels = rgb.shape

    # # red = 1, green = 2, blue = 3, none = 0
    # colorDict = {
    #       0: 0,
    #       1: 0,
    #       2: 0,
    #       3: 0
    # }

    # for i in range(height):
    #       for j in range(width):
    #             pixel = rgb[i, j]
    #             colorDict[classifyColor(pixel[0], pixel[1], pixel[2], shareThreshold)] += 1

    # return colorDict
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

# --- global task values --- #
rt = redTask("Task_Red", RotatoSettings.roundRobinQuant)
bt = blueTask("Task_Blue", RotatoSettings.roundRobinQuant)
gt = greenTask("Task_Green", RotatoSettings.roundRobinQuant)
tasks = [rt, gt, bt]

def main() :
    # --- Setup --- #
    currTime = 0.0
    lastTick = 0.0
    startTimestamp = current_milli_time()
    
   

    # --- image setup --- #
    global bot
    bot = Raspbot()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)


    StartupAction(bot)

    # --- update loop --- #
    taskQueue = deque([])
    tasksInQueue = {} # dict to keep track of queued tasks
    timeSliceCounter = 0
    while currTime < RotatoSettings.timeLimit:
        timeSliceCounter += 1
        currTime = current_milli_time() - startTimestamp
        hyperperiod = currTime + RotatoSettings.hyperperiodTime

        # --- per-update functions --- #
        # read camera
        ret, frame = cap.read()

        # threshold color
        colorResults, masks = ColorCounter(frame, RotatoSettings.colorThreshold) #TODO : change me
        colorIdx, colorPoint = ColorLocator(colorResults, masks)
        #colorIdx = max(colorResults, key = colorResults.get)
        print(f"Located centroid {colorPoint[0]}, {colorPoint[1]}")
        print(f"dominant color {colorIdx}")
        # if color threshold achieved and task not in queue, insert task into queue; make sure to add bookkeeping to tasksInQueue
        # otherwise do nothing
        # initialize the task being added too
        if colorIdx != 0:
            if taskQueue.count(colorIdx - 1) == 0:
                taskQueue.append(colorIdx - 1)
                tasks[colorIdx - 1].setup() # <-- UNCOMMENTED FROM PREVIOUS FIX

        # update PID targets based on current colors
        if (colorIdx == 3):
            PIDOutput_Blue = PIDController_Blue.updatePoint(colorPoint[0])
            blue_delta_value = colorPoint[0] - (config.FRAME_WIDTH)//2
        if (colorIdx == 2):
            PIDOutput_Green = PIDController_Green.updatePoint(colorPoint[0])
            green_delta_value = colorPoint[0] - (config.FRAME_WIDTH)//2
        print("timeslice: ", timeSliceCounter, ", color detected: ", colorIdx)

        # --- Round-robin --- #
        numTasks = len(taskQueue)
        for i in range(numTasks):
            nextTaskIdx = taskQueue.pop()
            print("task started: ", nextTaskIdx)
            
            result = tasks[nextTaskIdx].start() 
            #result = (currTime % 2) == 0
            if not result:
                taskQueue.append(nextTaskIdx)
                print("task re-added")
            else:
                print("task ended")
                #tasks[nextTaskIdx].reset()

        print("sleeping for ms: ", (hyperperiod - (current_milli_time() - startTimestamp)))
        time.sleep(max((hyperperiod - (current_milli_time() - startTimestamp)) / 1000, 0))

        # if no task currently executing, pop next task from the queue and execute
        # when time exceeds, move to next task (maybe reschedule task if it does not complete in time?)
        # if no tasks, do nothing

    # --- end --- #


if __name__ == "__main__":
    print("Starting program")
    main()
    print("Ending program")