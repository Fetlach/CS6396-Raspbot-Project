

from McLumk_Wheel_Sports import *
from Utils import current_milli_time, _angle_deg_from_errx
import RotatoSettings
import RobotState
import time

from Task import task
import config


class redTask(task):
    def __init__(self, name = "Suraj", quantTime = RotatoSettings.roundRobinQuant):
        super().__init__(name, 0, quantTime)
        self.IsActive = False

    def RedAction(self):
        self.setTimes(current_milli_time(), RotatoSettings.rot180Degree_time)

        if not self.IsActive:
            self.IsActive = True
            self.StopSpinningTimestamp = current_milli_time() + RotatoSettings.rot180Degree_time
        
        rotate_left(RotatoSettings.rot180Degree_speed)
         
        # KEEP SPINNING for as long as it takes for the bot to turn 180
        curTime = current_milli_time()
        while curTime < self.endTime:
          curTime = current_milli_time()
        
          # reached stop timestamp, so stop the robot
          if curTime > self.StopSpinningTimestamp: 
            stop_robot()
            self.IsActive = False