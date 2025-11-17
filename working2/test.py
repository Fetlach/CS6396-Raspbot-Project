import RobotState
import time
import RotatoSettings
import config
def main():
  try:
      RobotState.bot.rotate_in_place(RotatoSettings.rot180Degree_power)
      print(vars(RobotState.bot))
      time.sleep(1000)
      RobotState.bot.stop()
      time.sleep(1)
      # rotate_right(speed)
      # time.sleep(duration)
      # stop_robot()
      # time.sleep(1)

  except KeyboardInterrupt:
      # ????????,???????? When the user presses the stop button, the car stops moving.
          RobotState.bot.stop()
          print("off.")
  
  
  


if __name__ == "__main__":
    print("Starting program")
    #main()
    print(f"config = {config.FRAME_WIDTH//2}")
    print("Ending program")