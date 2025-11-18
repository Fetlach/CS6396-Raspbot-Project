import threading
import time
# our files
import RotatoSettings
import RobotState
from Utils import current_milli_time
import RobotState
import StartupAction
from ColorCounter_and_Locator import ColorCounter, ColorLocator
import cv2

from RedAction import redTask
from GreenAction import greenTask
from BlueAction import blueTask


def TimerCheck(currTime, startTimestamp):
  if (currTime - startTimestamp) > RotatoSettings.timeLimit:
    print("[Main] Time limit reached. Signaling shutdown...")
    return True
  return False