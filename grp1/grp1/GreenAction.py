

from McLumk_Wheel_Sports import *
from Utils import current_milli_time, _angle_deg_from_errx
import RotatoSettings
import RobotState
import time

from Task import task
import config


class greenTask(task):
    def __init__(self, name = "Suraj", quantTime = RotatoSettings.roundRobinQuant):
        super().__init__(name, 0, quantTime)
    
    def GreenAction(self, green_delta_value):
        self.setTimes(current_milli_time(), RotatoSettings.rot180Degree_time)

        speed = 100
        angle_deg = _angle_deg_from_errx(green_delta_value)
        duration = abs(angle_deg / config.SPIN_DEG_PER_SEC) / 2
        
        print(f"Duration is {duration}")
        print(f"GREEN DELTA VALUE IS {green_delta_value}")
        
        if green_delta_value < 0:
            rotate_left(speed)
        else:
            rotate_right(speed)
        
        # KEEP SPINNING for as long as it takes for the bot to turn and face the centroid
        curTime = current_milli_time()
        while curTime < self.endTime:
          curTime = current_milli_time()
          
          if abs(green_delta_value) < config.CAMERA_HDEADZONE_DEG:
            stop_robot()

        return
