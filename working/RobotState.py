from robot import Raspbot
class robotState:
    def __init__(self):
        redTaskActive = False
        blueTaskActive = False
        greenTaskActive = False
        currentRotation = 0.0


state = robotState()

bot = Raspbot()
blue_delta_value = 0
green_delta_value = 0