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
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)
# cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

blue_delta_value = 0
green_delta_value = 0

# -- queues and sets containing actions to run --- 
task_queue = queue.Queue(maxsize = 3)
tasks_in_queue = set()

# --- LOCKS ---

cap_lock = threading.Lock()

#--- Shutdown Event for threads ---
shutdown_event = threading.Event()