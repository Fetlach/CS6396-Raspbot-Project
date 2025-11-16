from RobotState import blue_delta_value, green_delta_value, robotState
from PIDController import PIDController_Blue, PIDController_Green
from McLumk_Wheel_Sports import *
from Utils import current_milli_time
import RotatoSettings
import RobotState
import time
import StartupAction
from Task import task
import config

bot = Raspbot()

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
        now = time.time()
        
        # If a timed rotation is already running, stop when time is up
        # if config.GREEN_CTRL.get("active"):
        #     if now >= GREEN_CTRL["until"]:
        #         bot.stop()
        #         GREEN_CTRL["active"] = False
        #     return

        # No active rotation → compute command from latest centroid
        centroid = RobotState.task_queue.get('centroid')
        if centroid is None:
            bot.stop()
            return

        cx, cy = centroid
        err_x = cx - (config.FRAME_WIDTH // 2)
        angle_deg = bot._angle_deg_from_errx(err_x)

        # Deadband to avoid jitter
        if abs(angle_deg) <= config.GREEN_DEG_TOL:
            bot.stop()
            return

        # Choose speed (clamped)
        speed = bot.clamp(
            config.ROTATE_SPEED_DEFAULT,
            config.ROTATE_SPEED_MIN,
            config.ROTATE_SPEED_MAX,
        )

        # Compute duration from spin rate; cap for safety
        deg_per_sec = max(1e-6, config.SPIN_DEG_PER_SEC)
        duration = min(abs(angle_deg) / deg_per_sec, config.GREEN_MAX_DURATION_S) / 2

        # Direction: +angle => target right => rotate RIGHT (CW)
        # Our HAL: rotate_in_place(+speed) = CCW/left, (-speed) = CW/right
        signed_speed = -speed if angle_deg > 0 else +speed

        # Start timed spin and remember when to stop

        if angle_deg > 0:
            rotate_right(speed)
        else:
            rotate_left(speed)
        #rotate_left(speed)  # wrapper calls rotate_left/right under the hood
        time.sleep(duration)
        stop_robot()

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
