import simple_pid
from RobotState import blue_delta_value, green_delta_value
class PIDManager:
    # https://simple-pid.readthedocs.io/en/latest/user_guide.html
    def __init__(self):
        self.my_pid = simple_pid.PID(1, 0.00, 0.05, setpoint=0)
        self.my_pid.sample_time = 0.01
        self.my_pid.output_limits = (-10, 10)    # Output value will be between 0 and 10
        self.goal = 0.0
        self.convergenceThreshold = 0.05
        self.convergenceUpdates = 25
        self.convergenceCounter = 0
     
    def updatePoint(self, v):
        self.my_pid.setpoint = v
        self.goal = v
    """
    def setNewPoint(self, v):
        self.my_pid.set_auto_mode(True, last_output=0.0)
        self.my_pid.setpoint = v
        self.goal = v
        self.convergenceCounter = 0
    """
        
        
    def update(self, value):
        currValue = self.my_pid(value)
        flag = False
        if (abs(currValue) < self.convergenceThreshold):
            self.convergenceCounter += 1
            flag = True
        else:
            self.convergenceCounter = 0
        if (self.convergenceCounter >= self.convergenceUpdates):
            self.convergenceCounter = 0
            self.disable()
        return currValue, flag

    def disable(self):
        self.my_pid.auto_mode = False

PIDController_Green = PIDManager()
PIDController_Blue = PIDManager()

PIDOutput_Green = 0.0
PIDOutput_Blue = 0.0
