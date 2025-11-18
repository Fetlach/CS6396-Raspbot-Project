from RobotState import blue_delta_value, green_delta_value, robotState
from PIDController import PIDController_Blue, PIDController_Green
from McLumk_Wheel_Sports import *
from Utils import current_milli_time, _angle_deg_from_errx
import RotatoSettings
import RobotState
import time
import StartupAction
from Task import task
import config

class redTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)
        self.endRotationTimestamp = 0

    # this is the red action
    # this action rotates the robot left for a certain amount of time that is saved on this task between time slices
    def RedAction(self, currTime, endTime)->bool:
        print("[RedAction] Starting 180-degree turn...")
        # rotate left until we reach our end time
        if (round(time.time() * 1000) < self.endRotationTimestamp):
            rotate_left(RotatoSettings.rot180Degree_speed)
            return False # because we have not finished rotating
        else:
            stop_robot()
            return True # because we have finished rotating
    
    # this function is the setup; it should be called once when the task is first activated
    # it sets a timestamp for when we'll need to stop in the future
    def setup(self):
        RobotState.state.redTaskActive = True
        self.endRotationTimestamp = round(time.time() * 1000) + (RotatoSettings.rot180Degree_time * 1000)
        
    # call this function to start the task for a timeslice once it has been set up
    # it handles anything we need to do before continuing to our update function (which loops over our red task)
    # and handles anything we need to do before returning
    def start(self)->bool:
        # things we need to set up before update loop
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        # update loop
        completed = self.update()

        # things we need to clean up before returning to round robin
        if completed:
            self.reset

        # return to round robin
        return completed
    
    # this function loops until our time slice for the task expires
    def update(self) -> bool:
        completed = False
        # we loop for the entire duration of the time slice we're given
        while (round(time.time() * 1000) < self.endTime):
            if completed:
                continue
            else:
                completed = self.RedAction(round(time.time() * 1000), self.endRotationTimestamp)
        
        # if false is returned, the task is still active and needs to remain instantiated
        # if true is returned, the task completed and needs to be reset or destroyed
        return completed 
    
    # we call this function after we've completed to clean up anything specific (like a destructor would)
    def reset(self):
        RobotState.state.redTaskActive = False

class greenTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)
        self.ReachedTarget = False
    
    def GreenAction(self, centroid)->bool:
        speed = 100
        
        print("Starting Green Task")
        print(f"Centroid is {centroid}")
        if not centroid:
          return
        
        cx, cy = centroid
        print (f"cx is {cx}")
        err_x = cx - (config.FRAME_WIDTH // 2 )
        
        angle_deg = _angle_deg_from_errx(err_x)
        duration = abs(angle_deg / config.SPIN_DEG_PER_SEC) / 2

        distance = _angle_deg_from_errx(abs(err_x))
        
        print(f"Duration is {duration}")
        print(f"GREEN DELTA VALUE IS {err_x}")
        
        stopped = False
        try:
          if distance < config.CAMERA_HDEADZONE_DEG:
              stop_robot()
              stopped = True
          elif err_x < 0:
              rotate_left(speed)
          else:
              rotate_right(speed)
        except KeyboardInterrupt:
          print("Interrupted by keyboard ctrl c")
          stop_robot()
        
        return stopped

    # the green action does not need to be set up since we're not managing a PID right now
    def setup(self):
        pass

    def start(self, centroid) -> bool:
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        # red task takes priority over this one
        # if it isn't active, then we're allowed to enter our update
        completed = False
        if not RobotState.state.redTaskActive:
            completed = self.update(centroid)
        else:
            time.sleep(max(self.endTime - current_milli_time(), 0))

        # clean up if we've completed
        if completed:
            self.reset()

        return completed
        
    def update(self, v) -> bool:
        while(current_milli_time() < self.endTime):
            self.GreenAction(v)
        return self.ReachedTarget
    
    def reset(self):
        RobotState.state.greenTaskActive = False

class blueTask(task):
    def __init__(self, name, quantTime):
        super().__init__(name, 0, quantTime)
        self.ReachedTarget = False

    def BlueAction(self, centroid)->bool:
        speed = 100
        
        print("Starting Blue Task")
        print(f"Centroid is {centroid}")
        if not centroid:
          return
        
        cx, cy = centroid
        print (f"cx is {cx}")
        err_x = cx - (config.FRAME_WIDTH // 2 )
        
        angle_deg = _angle_deg_from_errx(err_x)
        duration = abs(angle_deg / config.SPIN_DEG_PER_SEC) / 2
        
        print(f"Duration is {duration}")
        print(f"BLUE DELTA VALUE IS {err_x}")
        distance = _angle_deg_from_errx(abs(err_x))

        stopped = False
        try:
            if distance < config.CAMERA_HDEADZONE_DEG:
                stop_robot()
                stopped = True
            elif err_x < 0:
                move_right(speed)
            else:
                move_left(speed)
        except KeyboardInterrupt:
            print("Interrupted by keyboard ctrl c")
            stop_robot()
        
        return stopped
    
    def setup(self):
        pass
    
    def start(self, centroid) ->bool:
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        completed = False
        if not RobotState.state.redTaskActive and not RobotState.state.greenTaskActive:
            completed = self.update(centroid)
        else:
            time.sleep(max(self.endTime - current_milli_time(), 0))
        
        if completed:
            self.reset()

        return completed
        
    def update(self, centroid) -> bool:
        while(current_milli_time() < self.endTime):
            self.BlueAction(centroid)
        return self.ReachedTarget
    
    def reset(self):
        global state
        RobotState.state.blueTaskActive = False

# --- global task values --- #
rt = redTask("Task_Red", RotatoSettings.roundRobinQuant)
bt = blueTask("Task_Blue", RotatoSettings.roundRobinQuant)
gt = greenTask("Task_Green", RotatoSettings.roundRobinQuant)
tasks = [rt, gt, bt]
