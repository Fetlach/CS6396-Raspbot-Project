from RobotState import blue_delta_value, green_delta_value, robotState
from PIDController import PIDController_Blue, PIDController_Green
from McLumk_Wheel_Sports import *
from Utils import current_milli_time
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
        global PIDController_Green
        control, reached = PIDController_Green.update(green_delta_value)
        speed = round(abs(control) * RotatoSettings.rotGradual_power)
        if reached:
            RobotState.bot.stop()
        else:
            RobotState.bot.rotate_in_place(speed)
        
        self.ReachedTarget = reached

    def setup(self):
        global state
        global PIDController_Green
        global PIDOutput_Green
        RobotState.state.greenTaskActive = True
        #PIDController_Green.setNewPoint(PIDOutput_Green)
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
        global PIDController_Blue
        global PIDOutput_Blue
        RobotState.state.blueTaskActive = True
        #PIDController_Blue.setNewPoint(PIDOutput_Blue)
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
        global PIDController_Blue
        control, reached = PIDController_Blue.update(blue_delta_value)
        speed = round(control * RotatoSettings.moveSideways_power)
        if reached:
            RobotState.bot.stop()
        else:
            if blue_delta_value < 0:
              RobotState.bot.strafe(speed*(-1))
            else:
              RobotState.bot.strafe(speed)
        
        self.ReachedTarget = reached
        
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
