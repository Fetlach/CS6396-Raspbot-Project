import threading
from McLumk_Wheel_Sports import *
import threading
import time
from Task import task, redTask, blueTask, greenTask
import config
from robot import Raspbot
# our files
import RotatoSettings
from RobotState import blue_delta_value, green_delta_value, task_queue, tasks_in_queue, cap_lock, shutdown_event, cap
from Utils import current_milli_time
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
    delta = colorPoint[0] -  (config.FRAME_WIDTH) // 2
    if colorIdx == 2:
      green_delta_value = delta
    
    elif colorIdx == 3:
      blue_delta_value = delta
    
    if colorIdx != 0:
      if colorIdx not in tasks_in_queue:
        try:
          task_data = {
            'color' : colorIdx,
            'centroid' : colorPoint,
            'delta' : delta
          }
          task_queue.put(task_data, block = False)
          tasks_in_queue.add(colorIdx)
          print(f"[Thread 1] Pushed task {colorIdx} to queue.")
        
        except queue.Full:
          pass
     
    # limiting framerate
    time.sleep(0.033)
    
  
  print("[Thread 1] Shutdown signal received. Exiting.")
    
     
      
      
      
      
      
      