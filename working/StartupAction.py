from McLumk_Wheel_Sports import *# external libraries
import threading
import time
from robot import Raspbot
def StartupAction(bot: Raspbot, duration: float = 2.8):
    print("[StartupAction] Spinning to indicate init OK...")
    # total_deg = config.SPIN_DEG_TARGET
    # bot.spin_approx_degrees(total_deg, config.SPIN_POWER, config.SPIN_DEG_PER_SEC)
    # bot.sleep(config.SPIN_EXTRA_SAFETY)
    # bot.stop()
    speed = 100
    try:
        rotate_left(speed)
        time.sleep(duration)
        stop_robot()
        time.sleep(1)
        # rotate_right(speed)
        # time.sleep(duration)
        # stop_robot()
        # time.sleep(1)

    except KeyboardInterrupt:
        # ????????,???????? When the user presses the stop button, the car stops moving.
            stop_robot()
            print("off.")
    print("[StartupAction] Complete. Entering round-robin loop.")