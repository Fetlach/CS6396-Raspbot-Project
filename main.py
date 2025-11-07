import threading
import time
import cv2
from collections import deque
import RotatoSettings
from simple_pid import PID

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
    def __PIDManager__(self):
        self.pid = PID(1, 0.00, 0.05, setpoint=0)
        self.pid.sample_time = 0.01
        self.pid.output_limits = (-10, 10)    # Output value will be between 0 and 10
        self.goal = 0.0
        self.convergenceThreshold = 0.05
        self.convergenceUpdates = 25
        self.convergenceCounter = 0

    def setNewPoint(self, v):
        self.pid.set_auto_mode(True, last_output=0.0)
        self.pid.setpoint(v)
        self.goal = v
        self.convergenceCounter = 0

    def update(self, value):
        currValue = self.pid(value)
        if (abs(currValue) < self.convergenceThreshold):
            self.convergenceCounter += 1
        if (self.convergenceCounter >= self.convergenceUpdates):
            self.disable()
        return currValue, self.convergenceCounter >= self.convergenceUpdates

    def disable(self):
        self.pid.auto_mode = False

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

class task:
    def __task__(self, name, startTime, quantTime):
        self.name = name
        self.quantTime = quantTime
        self.endTime = startTime + quantTime

    def start(self) -> bool:
        pass

    def update(self) -> bool:
        pass

    def reset(self) -> bool:
        pass

class redTask(task):
    def __redTask__(self, name, quantTime):
        super().__init__(name, quantTime)
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
            
    def start(self) -> bool:
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
    
    def update(self) -> bool:
        while(current_milli_time() < self.endTime):
            self.RedAction()
        return self.stoppedSpinning
    
    def reset(self):
        global state
        state.redTaskActive = False


class greenTask(task):
    def __greenTask__(self, name, quantTime):
        super().__init__(name, quantTime)
        self.MovingLeft = False
        self.MovingRight = False
        self.ReachedTarget = False
    
    def GreenAction(self, x, y):
        control, reached = PIDController.update(x)
        speed = round(abs(control) * 100)
        if reached:
            stop_robot()
        elif (speed > 0):
            rotate_right(speed)
        else:
            rotate_left(speed)
        
        self.ReachedTarget = reached

    def start(self) -> bool:
        global state
        state.geeenTaskActive = True
        completed = False
        PIDController.setNewPoint()
        if not state.blueTaskActive:
            completed = self.update()
        else:
            sleep(self.endTime - current_milli_time())

        if completed:
            self.reset()
        return completed
        
    def update(self) -> bool:
        while(current_milli_time() < self.endTime):
            self.GreenAction()
        return self.ReachedTarget
    
    def reset(self):
        global state
        state.greenTaskActive = False

class blueTask(task):
    def __blueTask__(self, name, quantTime):
        super().__init__(name, quantTime)
        self.MovingLeft = False
        self.MovingRight = False
        self.ReachedTarget = False
    
    def start(self):
        global state
        state.blueTaskActive = True
        completed = False
        completed = self.update()
        
        if completed:
            self.reset()
        return completed

    def BlueAction(self, x, y):
        # if x < 0.4 move left
        # elif x > 0.6 move right
        # else return true
        pass
        
    def update(self) -> bool:
        while(current_milli_time() < self.endTime):
            self.BlueAction()
        return self.stoppedSpinning
    
    def reset(self):
        global state
        state.blueTaskActive = False

class imageState:
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

# --- global task values --- #
rt = redTask()
bt = blueTask()
gt = greenTask()
tasks = {rt, bt, gt}

def main() :
    # --- Setup --- #
    currTime = 0.0
    lastTick = 0.0

    # --- image setup --- #
    bot = Raspbot()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    try:
        startupAction(bot)

    # --- update loop --- #
    taskQueue = deque(task)
    tasksInQueue = {} # dict to keep track of queued tasks
    while currTime < RotatoSettings.timeLimit:
        currTime = current_milli_time()
        hyperperiod = currTime + RotatoSettings.hyperperiodTime

        # --- per-update functions --- #
        # read camera
        ret, frame = cap.read()

        # threshold color
        colorResults = ColorCounter(frame) #TODO : change me
        colorIdx = max(colorResults, key = colorResults.get)
        colorPoint = ColorLocator(colorResults)

        # update PID targets based on current colors
        if (colorIdx == 3):
            PIDOutput_Blue = PIDController_Blue(colorPoint[0])
        if (colorIdx == 2):
            PIDOutput_Green = PIDController_Green(colorPoint[0])

        # if color threshold achieved and task not in queue, insert task into queue; make sure to add bookkeeping to tasksInQueue
        # otherwise do nothing
        if colorIdx is not 0:
            currTask = tasks[colorIdx - 1]
            if taskQueue.count(currTask) is 0:
                taskQueue.append(currTask)

        # --- Round-robin --- #
        numTasks = len(taskQueue)
        for i in range(numTasks):
            nextTask = taskQueue.pop()
            result = nextTask.start()
            if not result:
                taskQueue.append(nextTask)

        sleep(hyperperiod - current_milli_time())

        # if no task currently executing, pop next task from the queue and execute
        # when time exceeds, move to next task (maybe reschedule task if it does not complete in time?)
        # if no tasks, do nothing

    # --- end --- #


if __name__ == "__main__":
    print("Starting program")
    main()
    print("Ending program")
