from McLumk_Wheel_Sports import *# external libraries
import threading
import time
from robot import Raspbot
def StartupAction(duration: float = 2.8):
    print("[StartupAction] Spinning to indicate init OK...")
    
    speed = 100
    rotate_left(speed)
    time.sleep(duration)
    stop_robot()
    time.sleep(1)
 

   
    print("[StartupAction] Complete. Entering round-robin loop.")