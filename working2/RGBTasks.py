from RobotState import blue_delta_value, green_delta_value, robotState
from PIDController import PIDController_Blue, PIDController_Green
from McLumk_Wheel_Sports import *
from Utils import current_milli_time, _angle_deg_from_errx
import RotatoSettings
import RobotState
import time
import StartupAction
from Task import task
class redTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)

    def RedAction(self):
        
        print("[RedAction] Starting 180-degree turn...")
        try:
            rotate_left(RotatoSettings.rot180Degree_speed)
            time.sleep(RotatoSettings.rot180Degree_time)
            stop_robot()
            # rotate_right(speed)
            # time.sleep(duration)
            # stop_robot()
            # time.sleep(1)
        except KeyboardInterrupt:
            # ????????,???????? When the user presses the stop button, the car stops moving.
                stop_robot()
                print("off.")
        
            
        
            
    def start(self) -> bool:
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        # --- update task and global state --- #
        if RobotState.state.redTaskActive:
            # already active
            pass
        else:
            # not active - initialize
            self.startedSpinning = False
            self.stoppedSpinning = False
            self.stopSpinTimestamp = current_milli_time() + RotatoSettings.rot180Degree_time
            RobotState.state.redTaskActive = True
        
        # check if can enter update loop
        completed = False
        if not RobotState.state.greenTaskActive and not RobotState.state.blueTaskActive:
            completed = self.update()
        else:
            time.sleep(self.endTime - current_milli_time())

        # check if completed, reset if so
        if completed:
            self.reset()
        return completed
    
    def setup(self):
        pass
    
    def update(self) -> bool:
        RobotState.state.redTaskActive = True
        self.RedAction()
        return True
    
    def reset(self):
        
        RobotState.state.redTaskActive = False

class greenTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)
        self.ReachedTarget = False
    
    def GreenAction(self):
        speed = 100

        angle_deg = _angle_deg_from_errx(green_delta_value)
        duration = abs(angle_deg / config.SPIN_DEG_PER_SEC) / 2
        if green_delta_value < 0:
            rotate_left(speed)
        else:
            rotate_right(speed)
        
        time.sleep(duration)
        stop_robot()

    def setup(self):
        global state
        RobotState.state.greenTaskActive = True
        self.ReachedTarget = False

    def start(self) -> bool:
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        completed = False
        
        if not RobotState.state.blueTaskActive:
            completed = self.update()
        
        time.sleep(max(self.endTime - current_milli_time(), 0))
        return completed
        
    def update(self) -> bool:
        while(current_milli_time() < self.endTime):
            self.GreenAction()
        return self.ReachedTarget
    
    def reset(self):
        RobotState.state.greenTaskActive = False

class blueTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)
        self.ReachedTarget = False

    def setup(self):
        global state
        RobotState.state.blueTaskActive = True
        self.ReachedTarget = False
    
    def start(self):
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        completed = False
        completed = self.update()
        
        if completed:
            self.reset()

        time.sleep(max(self.endTime - current_milli_time(), 0))
        return completed

    def BlueAction(self):
        speed = 100

        angle_deg = _angle_deg_from_errx(green_delta_value)
        duration = abs(angle_deg / config.SPIN_DEG_PER_SEC) / 2
        if blue_delta_value < 0:
            move_left(speed)
        else:
            move_right(speed)
        
        time.sleep(duration)
        stop_robot()
        
    def update(self) -> bool:
        while(current_milli_time() < self.endTime):
            self.BlueAction()
        return self.ReachedTarget
    
    def reset(self):
        global state
        RobotState.state.blueTaskActive = False



# --- global task values --- #
rt = redTask("Task_Red", RotatoSettings.roundRobinQuant)
bt = blueTask("Task_Blue", RotatoSettings.roundRobinQuant)
gt = greenTask("Task_Green", RotatoSettings.roundRobinQuant)
tasks = [rt, gt, bt]
