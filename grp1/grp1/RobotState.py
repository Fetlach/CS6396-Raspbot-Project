from robot import Raspbot
import threading
import cv2
import config
import queue
class robotState:
    def __init__(self):
        self.redTaskActive = False
        self.blueTaskActive = False
        self.greenTaskActive = False
        self.currentRotation = 0.0


state = robotState()

bot = Raspbot()


