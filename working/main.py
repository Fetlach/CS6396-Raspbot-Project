import threading
import cv2
from collections import deque
import simple_pid
from McLumk_Wheel_Sports import *
import threading
import time
from PIDController import PIDController_Blue, PIDController_Green, PIDManager
from RGBTasks import redTask, blueTask, greenTask
import config
from robot import Raspbot
# our files
import RotatoSettings
from RobotState import blue_delta_value, green_delta_value
from Utils import current_milli_time
import RobotState
# allows for controlling input according to keyboard
debug = True
import StartupAction
from ColorCounter_and_Locator import ColorCounter, ColorLocator

import queue # <-----Thread safe implementation of queue


def main() :



    
    # -- Create kill switch for all the threads ---
    shutdown_event = threading.Event()
    
    
   

    # --- Setup Hardware --- #
    
    bot = RobotState.bot
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    
    
    #--- Startup Spin ---
    StartupAction.StartupAction(bot)
    

    # ---  STart the Vision Thread and the Action Thread ---
    
    vision_thread = threading.Thread(target = vision_thread_loop, args = (shutdown_event,))
    action_thread = Threading.thread(target = action_thread_loop, args = (shutdown_event, ))
    
    vision_thread.start()
    action_thread.start()
    
    startTimestamp = current_milli_time()
    try:
      while True:
        currTime = current_milli_time()
        
        #Check if time limit reached
        if (currTime - startTimeStamp) > RotatoSettings.timeLimit:
          print("[Main] Time limit reached. Signaling shutdown...")
          break
        
        if not vision_thread.is_alive() or not action_thread.is_alive():
          print("[Main] A worker thread has died. Signaling Shutdown...")
          break
        
        time.sleep(0.5)
    
    except KeyboardInterrupt:
      print("\n[Main] KeyboardInterrupt. Signaling shutdown...")
    
    
    # --- Cleanup ---
    shutdown_event.set()
    print("[Main] Waiting for threads to exit...")
    vision_thread.join()
    action_thread.join()

    # 3. Clean up hardware
    print("[Main] All threads closed. Cleaning up hardware.")
    cap.release()
    bot.stop()
    print("[Main] Program ended.")
    
    


if __name__ == "__main__":
    print("Starting program")
    main()
    print("Ending program")