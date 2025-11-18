

from McLumk_Wheel_Sports import *
from Utils import current_milli_time, _angle_deg_from_errx
import RotatoSettings
import RobotState
import time

from Task import task
import config

def IdleAction():
  endTime = current_milli_time() + RotatoSettings.roundRobinQuant
  curTime = current_milli_time()
  stop_robot()
  
  # KEEP SPINNING for as long as it takes for the bot to turn 180
  while curTime < endTime:
    curTime = current_milli_time()
    pass
  
