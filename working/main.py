# external libraries
import threading
import time
import cv2
from collections import deque
import simple_pid
from McLumk_Wheel_Sports import *# external libraries
import threading
import time
import cv2
from collections import deque
import simple_pid
from McLumk_Wheel_Sports import *
import config
from robot import Raspbot
from vision import count_colors_and_masks, largest_color, centroid_from_mask
# our files
import RotatoSettings

# allows for controlling input according to keyboard
debug = True

def current_milli_time():
    return round(time.time() * 1000)

# how to use:
# - Set to a target delta (IE: position of the midpoint) with setNewPoint
#   - (internal PID is set to a zero position each time)
#   - This also enables the PID
# - call update every n seconds, use output to drive motors; will return false as second output when moving
#   - PID likes fixed timestepping, so need to reset if delayed to much
# - once the PID converges for n updates it will return true as the second output of the update function
#   - It will automatically disable itself once this happens

class PIDManager:
    # https://simple-pid.readthedocs.io/en/latest/user_guide.html
    def __init__(self):
        self.my_pid = simple_pid.PID(1, 0.00, 0.05, setpoint=0)
        self.my_pid.sample_time = 0.01
        self.my_pid.output_limits = (-10, 10)    # Output value will be between 0 and 10
        self.goal = 0.0
        self.convergenceThreshold = 0.05
        self.convergenceUpdates = 25
        self.convergenceCounter = 0

    def updatePoint(self, v):
        self.my_pid.setpoint = v
        self.goal = v

    def setNewPoint(self, v):
        self.my_pid.set_auto_mode(True, last_output=0.0)
        self.my_pid.setpoint = v
        self.goal = v
        self.convergenceCounter = 0

    def update(self, value):
        currValue = self.my_pid(value)
        if (abs(currValue) < self.convergenceThreshold):
            self.convergenceCounter += 1
        if (self.convergenceCounter >= self.convergenceUpdates):
            self.disable()
        return currValue, self.convergenceCounter >= self.convergenceUpdates

    def disable(self):
        self.my_pid.auto_mode = False

PIDController_Green = PIDManager()
PIDController_Blue = PIDManager()

PIDOutput_Green = 0.0
PIDOutput_Blue = 0.0

class robotState:
    def __robotState__(self):
        redTaskActive = False
        blueTaskActive = False
        greenTaskActive = False
        currentRotation = 0.0
        
state = robotState()
bot = Raspbot()

class task:
    def __init__(self, name, startTime, quantTime):
        self.name = name
        self.quantTime = quantTime
        self.endTime = startTime + quantTime

    def setTimes(self, startTime, quantTime):
        self.quantTime = quantTime
        self.endTime = startTime + quantTime

    def setup(self):
        pass

    def start(self, cap) -> bool: # <-- CHANGED (added cap)
        pass

    def update(self) -> bool:
        pass

    def reset(self) -> bool:
        pass

class redTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)
        self.startedSpinning = False
        self.stoppedSpinning = False
        self.stopSpinTimestamp = 0.0

    def RedAction(self):
        if (self.startedSpinning == False):
            # apply wheel power
            self.startedSpinning = True
            self.stopSpinTimestamp = current_milli_time() + RotatoSettings.rot180Degree_time
        elif (self.stoppedSpinning == False and current_milli_time() > self.stopSpinTimestamp) :
            # stop wheel power
            self.stoppedSpinning = True
            
    def start(self, cap) -> bool: # <-- CHANGED (added cap)
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        # --- update task and global state --- #
        global state
        if state.redTaskActive:
            # already active
            pass
        else:
            # not active - initialize
            self.startedSpinning = False
            self.stoppedSpinning = False
            self.stopSpinTimestamp = current_milli_time() + RotatoSettings.rot180Degree_time
            state.redTaskActive = True
        
        # check if can enter update loop
        completed = False
        if not state.greenTaskActive and not state.blueTaskActive:
            completed = self.update()
        else:
            sleep(self.endTime - current_milli_time())

        # check if completed, reset if so
        if completed:
            self.reset()
        return completed
    
    def setup():
        pass
    
    def update(self) -> bool:
        while(current_milli_time() < self.endTime):
            self.RedAction()
        return self.stoppedSpinning
    
    def reset(self):
        global state
        state.redTaskActive = False

class greenTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)
        self.ReachedTarget = False
    
    def GreenAction(self, x, y):
        global bot
        global PIDController_Green
        control, reached = PIDController_Green.update(x)
        speed = round(abs(control) * RotatoSettings.rotGradual_power)
        if reached:
            bot.stop()
        else:
            bot.rotate_in_place(speed)
        
        self.ReachedTarget = reached

    def setup(self):
        global state
        global PIDController_Green
        global PIDOutput_Green
        state.greenTaskActive = True
        PIDController_Green.setNewPoint(PIDOutput_Green)
        self.ReachedTarget = False

    def start(self, cap) -> bool: # <-- CHANGED (added cap)
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        completed = False
        if not state.blueTaskActive:
            completed = self.update(cap) # <-- CHANGED (passed cap)
        
        sleep(max(self.endTime - current_milli_time(), 0))
        return completed
        
    def update(self, cap) -> bool: # <-- CHANGED (added cap)
        while(current_milli_time() < self.endTime):
            
            # --- ADDED: Read camera and find color --- #
            ret, frame = cap.read()
            if not ret:
                continue # Skip if frame read fails
            colorResults, masks = ColorCounter(frame, RotatoSettings.colorThreshold)
            colorIdx, colorPoint = ColorLocator(colorResults, masks)
            # ------------------------------------ #
            
            # --- CHANGED: Pass args and check color --- #
            if colorIdx == 2: # Only move if we still see green
                self.GreenAction(colorPoint[0], colorPoint[1])
            else:
                bot.stop() # Target lost, stop
                self.ReachedTarget = False # No longer on target
            
        return self.ReachedTarget
    
    def reset(self):
        global state
        state.greenTaskActive = False

class blueTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)
        self.ReachedTarget = False

    def setup(self):
        global state
        global PIDController_Blue
        global PIDOutput_Blue
        state.blueTaskActive = True
        PIDController_Blue.setNewPoint(PIDOutput_Blue)
        self.ReachedTarget = False
    
    def start(self, cap): # <-- CHANGED (added cap)
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        completed = False
        completed = self.update(cap) # <-- CHANGED (passed cap)
        
        if completed:
            self.reset()

        sleep(max(self.endTime - current_milli_time(), 0))
        return completed

    def BlueAction(self, x, y):
        global bot
        global PIDController_Blue
        control, reached = PIDController_Blue.update(x)
        speed = round(control * RotatoSettings.moveSideways_power)
        if reached:
            bot.stop()
        else:
            bot.strafe(speed)
        
        self.ReachedTarget = reached
        
    def update(self, cap) -> bool: # <-- CHANGED (added cap)
        while(current_milli_time() < self.endTime):
            
            # --- ADDED: Read camera and find color --- #
            ret, frame = cap.read()
            if not ret:
                continue # Skip if frame read fails
            colorResults, masks = ColorCounter(frame, RotatoSettings.colorThreshold)
            colorIdx, colorPoint = ColorLocator(colorResults, masks)
            # ------------------------------------ #

            # --- CHANGED: Pass args and check color --- #
            if colorIdx == 3: # Only move if we still see blue
                self.BlueAction(colorPoint[0], colorPoint[1])
            else:
                bot.stop() # Target lost, stop
                self.ReachedTarget = False # No longer on target
                
        return self.ReachedTarget
    
    def reset(self):
        global state
        state.blueTaskActive = False

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

    # --- global variables --- #
    global PIDController_Green
    global PIDController_Blue
    global PIDOutput_Green
    global PIDOutput_Blue

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
        if (colorIdx == 2):
            PIDOutput_Green = PIDController_Green.updatePoint(colorPoint[0])

        print("timeslice: ", timeSliceCounter, ", color detected: ", colorIdx)

        # --- Round-robin --- #
        numTasks = len(taskQueue)
        for i in range(numTasks):
            nextTaskIdx = taskQueue.pop()
            print("task started: ", nextTaskIdx)
            result = tasks[nextTaskIdx].start(cap) # <-- CHANGED (passed cap)
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
import config
from robot import Raspbot
from vision import count_colors_and_masks, largest_color, centroid_from_mask
# our files
import RotatoSettings

# allows for controlling input according to keyboard
debug = True

def current_milli_time():
    return round(time.time() * 1000)

# how to use:
# - Set to a target delta (IE: position of the midpoint) with setNewPoint
#   - (internal PID is set to a zero position each time)
#   - This also enables the PID
# - call update every n seconds, use output to drive motors; will return false as second output when moving
#   - PID likes fixed timestepping, so need to reset if delayed to much
# - once the PID converges for n updates it will return true as the second output of the update function
#   - It will automatically disable itself once this happens

class PIDManager:
    # https://simple-pid.readthedocs.io/en/latest/user_guide.html
    def __init__(self):
        self.my_pid = simple_pid.PID(1, 0.00, 0.05, setpoint=0)
        self.my_pid.sample_time = 0.01
        self.my_pid.output_limits = (-10, 10)    # Output value will be between 0 and 10
        self.goal = 0.0
        self.convergenceThreshold = 0.05
        self.convergenceUpdates = 25
        self.convergenceCounter = 0

    def updatePoint(self, v):
        self.my_pid.setpoint = v
        self.goal = v

    def setNewPoint(self, v):
        self.my_pid.set_auto_mode(True, last_output=0.0)
        self.my_pid.setpoint = v
        self.goal = v
        self.convergenceCounter = 0

    def update(self, value):
        currValue = self.my_pid(value)
        if (abs(currValue) < self.convergenceThreshold):
            self.convergenceCounter += 1
        if (self.convergenceCounter >= self.convergenceUpdates):
            self.disable()
        return currValue, self.convergenceCounter >= self.convergenceUpdates

    def disable(self):
        self.my_pid.auto_mode = False

PIDController_Green = PIDManager()
PIDController_Blue = PIDManager()

PIDOutput_Green = 0.0
PIDOutput_Blue = 0.0

class robotState:
    def __robotState__(self):
        redTaskActive = False
        blueTaskActive = False
        greenTaskActive = False
        currentRotation = 0.0
        
state = robotState()
bot = Raspbot()

class task:
    def __init__(self, name, startTime, quantTime):
        self.name = name
        self.quantTime = quantTime
        self.endTime = startTime + quantTime

    def setTimes(self, startTime, quantTime):
        self.quantTime = quantTime
        self.endTime = startTime + quantTime

    def setup(self):
        pass

    def start(self, cap) -> bool: # <-- CHANGED (added cap)
        pass

    def update(self) -> bool:
        pass

    def reset(self) -> bool:
        pass

class redTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)
        self.startedSpinning = False
        self.stoppedSpinning = False
        self.stopSpinTimestamp = 0.0

    def RedAction(self):
        if (self.startedSpinning == False):
            # apply wheel power
            self.startedSpinning = True
            self.stopSpinTimestamp = current_milli_time() + RotatoSettings.rot180Degree_time
        elif (self.stoppedSpinning == False and current_milli_time() > self.stopSpinTimestamp) :
            # stop wheel power
            self.stoppedSpinning = True
            
    def start(self, cap) -> bool: # <-- CHANGED (added cap)
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        # --- update task and global state --- #
        global state
        if state.redTaskActive:
            # already active
            pass
        else:
            # not active - initialize
            self.startedSpinning = False
            self.stoppedSpinning = False
            self.stopSpinTimestamp = current_milli_time() + RotatoSettings.rot180Degree_time
            state.redTaskActive = True
        
        # check if can enter update loop
        completed = False
        if not state.greenTaskActive and not state.blueTaskActive:
            completed = self.update()
        else:
            sleep(self.endTime - current_milli_time())

        # check if completed, reset if so
        if completed:
            self.reset()
        return completed
    
    def setup():
        pass
    
    def update(self) -> bool:
        while(current_milli_time() < self.endTime):
            self.RedAction()
        return self.stoppedSpinning
    
    def reset(self):
        global state
        state.redTaskActive = False

class greenTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)
        self.ReachedTarget = False
    
    def GreenAction(self, x, y):
        global bot
        global PIDController_Green
        control, reached = PIDController_Green.update(x)
        speed = round(abs(control) * RotatoSettings.rotGradual_power)
        if reached:
            bot.stop()
        else:
            bot.rotate_in_place(speed)
        
        self.ReachedTarget = reached

    def setup(self):
        global state
        global PIDController_Green
        global PIDOutput_Green
        state.greenTaskActive = True
        PIDController_Green.setNewPoint(PIDOutput_Green)
        self.ReachedTarget = False

    def start(self, cap) -> bool: # <-- CHANGED (added cap)
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        completed = False
        if not state.blueTaskActive:
            completed = self.update(cap) # <-- CHANGED (passed cap)
        
        sleep(max(self.endTime - current_milli_time(), 0))
        return completed
        
    def update(self, cap) -> bool: # <-- CHANGED (added cap)
        while(current_milli_time() < self.endTime):
            
            # --- ADDED: Read camera and find color --- #
            ret, frame = cap.read()
            if not ret:
                continue # Skip if frame read fails
            colorResults, masks = ColorCounter(frame, RotatoSettings.colorThreshold)
            colorIdx, colorPoint = ColorLocator(colorResults, masks)
            # ------------------------------------ #
            
            # --- CHANGED: Pass args and check color --- #
            if colorIdx == 2: # Only move if we still see green
                self.GreenAction(colorPoint[0], colorPoint[1])
            else:
                bot.stop() # Target lost, stop
                self.ReachedTarget = False # No longer on target
            
        return self.ReachedTarget
    
    def reset(self):
        global state
        state.greenTaskActive = False

class blueTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)
        self.ReachedTarget = False

    def setup(self):
        global state
        global PIDController_Blue
        global PIDOutput_Blue
        state.blueTaskActive = True
        PIDController_Blue.setNewPoint(PIDOutput_Blue)
        self.ReachedTarget = False
    
    def start(self, cap): # <-- CHANGED (added cap)
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        completed = False
        completed = self.update(cap) # <-- CHANGED (passed cap)
        
        if completed:
            self.reset()

        sleep(max(self.endTime - current_milli_time(), 0))
        return completed

    def BlueAction(self, x, y):
        global bot
        global PIDController_Blue
        control, reached = PIDController_Blue.update(x)
        speed = round(control * RotatoSettings.moveSideways_power)
        if reached:
            bot.stop()
        else:
            bot.strafe(speed)
        
        self.ReachedTarget = reached
        
    def update(self, cap) -> bool: # <-- CHANGED (added cap)
        while(current_milli_time() < self.endTime):
            
            # --- ADDED: Read camera and find color --- #
            ret, frame = cap.read()
            if not ret:
                continue # Skip if frame read fails
            colorResults, masks = ColorCounter(frame, RotatoSettings.colorThreshold)
            colorIdx, colorPoint = ColorLocator(colorResults, masks)
            # ------------------------------------ #

            # --- CHANGED: Pass args and check color --- #
            if colorIdx == 3: # Only move if we still see blue
                self.BlueAction(colorPoint[0], colorPoint[1])
            else:
                bot.stop() # Target lost, stop
                self.ReachedTarget = False # No longer on target
                
        return self.ReachedTarget
    
    def reset(self):
        global state
        state.blueTaskActive = False

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

    # --- global variables --- #
    global PIDController_Green
    global PIDController_Blue
    global PIDOutput_Green
    global PIDOutput_Blue

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
        if (colorIdx == 2):
            PIDOutput_Green = PIDController_Green.updatePoint(colorPoint[0])

        print("timeslice: ", timeSliceCounter, ", color detected: ", colorIdx)

        # --- Round-robin --- #
        numTasks = len(taskQueue)
        for i in range(numTasks):
            nextTaskIdx = taskQueue.pop()
            print("task started: ", nextTaskIdx)
            result = tasks[nextTaskIdx].start(cap) # <-- CHANGED (passed cap)
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