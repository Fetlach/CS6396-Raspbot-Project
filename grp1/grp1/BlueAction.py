

from McLumk_Wheel_Sports import *
from Utils import current_milli_time, _angle_deg_from_errx
import RotatoSettings
import RobotState
import time

from Task import task
import config

class blueTask(task):
    def __init__(self, name = "Suraj", quantTime = RotatoSettings.roundRobinQuant):
        super().__init__(name, 0, quantTime)
        self.IsActive = False

    def BlueAction(self, blue_delta_value):
        self.setTimes(current_milli_time(), RotatoSettings.roundRobinQuant)

        speed = 100
        angle_deg = _angle_deg_from_errx(blue_delta_value)
        duration = abs(angle_deg / config.SPIN_DEG_PER_SEC) / 2
        
        print(f"Duration is {duration}")
        print(f"BLUE DELTA VALUE IS {blue_delta_value}")
        
        if blue_delta_value < 0:
            move_right(speed)
        else:
            move_left(speed)
        
        endTime = current_milli_time() + duration
        curTime = current_milli_time()
        
        # KEEP SPINNING for as long as it takes for the bot to strafe and face the centroid
        curTime = current_milli_time()
        while curTime < self.endTime:
            curTime = current_milli_time()
            if abs(blue_delta_value) < config.CAMERA_HDEADZONE_DEG:
                stop_robot()

        return


