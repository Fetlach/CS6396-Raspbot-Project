import threading
import time
# our files
import RotatoSettings
from RobotState import blue_delta_value, green_delta_value, bot, shutdown_event, cap
import RobotState
from Utils import current_milli_time
import RobotState
# allows for controlling input according to keyboard
debug = True
import StartupAction
from ColorCounter_and_Locator import ColorCounter, ColorLocator
from VisionThread import vision_thread_loop
from ActionThread import action_thread_loop
import cv2

import queue # <-----Thread safe implementation of queue




def main() :
    
    #--- Startup Spin ---
    StartupAction.StartupAction(bot)
    

    # ---  STart the Vision Thread and the Action Thread ---
    
    vision_thread = threading.Thread(target = vision_thread_loop, args = (RobotState.shutdown_event,))
    action_thread = threading.Thread(target = action_thread_loop, args = (RobotState.shutdown_event,))
    
    vision_thread.start()
    action_thread.start()
    
    startTimestamp = current_milli_time()
    try:
      while True:
        currTime = current_milli_time()
        
        #Check if time limit reached
        if (currTime - startTimestamp) > RotatoSettings.timeLimit:
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