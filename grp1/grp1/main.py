
import time
# our files
import RotatoSettings
import RobotState
from Utils import current_milli_time
import RobotState
from StartupAction import StartupAction
from ColorCounter_and_Locator import ColorCounter, ColorLocator
import cv2
from TimerCheck import TimerCheck
from RedAction import redTask
from GreenAction import greenTask
from BlueAction import blueTask
from IdleAction import IdleAction
import config

task_queue = []

tasks_in_queue = set()


def main() :
    
    #--- Startup Spin ---
    StartupAction()
  
    startTimestamp = current_milli_time()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    
    while True:
      currTime = current_milli_time()
      
      #Check if timelimit reached (TIMERCHECK)
      if TimerCheck(currTime, startTimestamp):
        break
      
      ret, frame = cap.read()
      
      # COLOR COUNTER AND COLOR LOCATOR
      colorResults, masks = ColorCounter(frame, RotatoSettings.colorThreshold)
      colorIdx, colorPoint = ColorLocator(colorResults, masks)
      
      delta = colorPoint[0] -  (config.FRAME_WIDTH) // 2
      
      # Running the right task depending on the color detected and the color centroid
      if colorIdx == 0:
        IdleAction()
      
      elif colorIdx == 1:
        red = redTask()
        red.RedAction()
      
      elif colorIdx == 2:
        green_delta_value = delta
        green = greenTask()
        green.GreenAction(green_delta_value)
      
      else:
        blue_delta_value = delta
        blue = blueTask()
        blue.BlueAction(blue_delta_value)

    cap.release()
    
    


if __name__ == "__main__":
    print("Starting program")
    main()
    print("Ending program")