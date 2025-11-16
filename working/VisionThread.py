import threading
import cv2
import simple_pid
from McLumk_Wheel_Sports import *
import threading
import time
from PIDController import PIDController_Blue, PIDController_Green, PIDManager
from Task import task, redTask, blueTask, greenTask
import config
from robot import Raspbot
# our files
import RotatoSettings
from RobotState import blue_delta_value, green_delta_value
from Utils import current_milli_time
import RobotState
# allows for controlling input according to keyboard
debug = True
from ColorCounter_and_Locator import ColorCounter, ColorLocator

import queue # <-----Thread safe implementation of queue


def vision_thread_loop():
  """
    This function runs in its own thread.
    Its only job is to read the camera and push unique tasks to the queue.
    """
  print("[Thread 1] Vision Thread started.")
  while not shutdown_event.is_set():
    frame = None
    ret = False
    
    with cap_lock:
      ret, frame = cap.read()
    
    if not ret:
      print("[Thread 1] Error: Failed to read camera frame.")
      time.sleep(0.5)
      continue
    
    colorResults, masks = ColorCounter(frame, RotatoSettings.colorThreshold)
    colorIdx, colorPoint = ColorLocator(colorResults, masks)
     print(f"Located centroid {colorPoint[0]}, {colorPoint[1]}")
     print(f"dominant color {colorIdx}")
     
     blue_delta_value = colorPoint[0] - (config.FRAME_WIDTH)//2
     green_delta_value 
     
      
      
      
      
      
      