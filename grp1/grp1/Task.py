

from McLumk_Wheel_Sports import *
from Utils import current_milli_time
import RotatoSettings
import RobotState
import time
import StartupAction



class task:
    def __init__(self, name, startTime, quantTime):
        self.name = name
        self.quantTime = quantTime
        self.endTime = startTime + quantTime

    def setTimes(self, startTime, quantTime):
        self.quantTime = quantTime
        self.endTime = startTime + quantTime

    def setup(self):
        pass

    def start(self) -> bool:
        pass

    def update(self) -> bool:
        pass

    def reset(self) -> bool:
        pass


