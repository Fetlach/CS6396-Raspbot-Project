# CE 6308 / Project 1: Round-Robin RTOS for RASPBOT v2
# Uses cooperative round-robin scheduling across task functions.

import time
from typing import Optional, Dict, Tuple
import cv2
import numpy as np

import sys
sys.path.append('/home/pi/project_demo/lib')
from McLumk_Wheel_Sports import *

import config
from robot import Raspbot
from vision import count_colors_and_masks, largest_color, centroid_from_mask

IDLE = None  # sentinel for no active command

# ---------------- Task Functions ----------------

def StartupAction(bot: Raspbot):
    print("[StartupAction] Spinning to indicate init OK...")
    # total_deg = config.SPIN_DEG_TARGET
    # bot.spin_approx_degrees(total_deg, config.SPIN_POWER, config.SPIN_DEG_PER_SEC)
    # bot.sleep(config.SPIN_EXTRA_SAFETY)
    # bot.stop()
    duration = 2.8
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
        # 当用户按下停止时，停止小车运动功能 When the user presses the stop button, the car stops moving.
            stop_robot()
            print("off.")
    print("[StartupAction] Complete. Entering round-robin loop.")

def TimerCheck(start_time: float) -> bool:
    elapsed = time.time() - start_time
    if elapsed > config.MAX_RUNTIME_S:
        print(f"[TimerCheck] Max runtime {config.MAX_RUNTIME_S}s exceeded. Stopping.")
        return False
    return True

def classifyColor(r, g, b, shareThreshold) -> int:
    # red = 1, green = 2, blue = 3, none = 0
    value = float(r) + float(g) + float(b)
    rshare = float(r) / float(value)
    gshare = float(g) / float(value)
    bshare = float(b) / float(value)
    if rshare > gshare and rshare > bshare and rshare > shareThreshold:
        return 1
    elif gshare > rshare and gshare > bshare and gshare > shareThreshold:
        return 2
    elif bshare > rshare and bshare > gshare and bshare > shareThreshold:
        return 3
    else:
        return 0

def ColorCounter(frame_bgr):
    counts, masks = count_colors_and_masks(frame_bgr)
    print(f"[ColorCounter] counts={counts}")
    return counts, masks

def ColorLocator(counts: Dict[str,int], masks):
    dom = largest_color(counts)
    if dom is None:
        print("[ColorLocator] No dominant color (idle).")
        return None, None
    centroid = centroid_from_mask(masks[dom])
    if centroid is None:
        print("[ColorLocator] Dominant color but centroid not found -> idle.")
        return dom, None
    print(f"[ColorLocator] dominant={dom}, centroid={centroid}")
    return dom, centroid

def IdleAction(bot: Raspbot):
    bot.stop()

def _bounded_power(p, pmin, pmax):
    p_clamped = clamp(p, -pmax, pmax)
    return p_clamped if abs(p_clamped) >= pmin else 0.0

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def _angle_deg_from_errx(err_x: int) -> float:
    """
    Convert horizontal pixel error to approximate yaw angle (degrees).
    +angle => target is to the RIGHT of center (needs CW/right rotation).
    """
    half_w = config.FRAME_WIDTH / 2.0
    half_fov = config.CAMERA_HFOV_DEG / 2.0
    # err_x is positive when centroid is right of center
    return (err_x / half_w) * half_fov

def GreenAction(bot: Raspbot, centroid, GREEN_CTRL):
    now = time.time()
    
    # If a timed rotation is already running, stop when time is up
    if GREEN_CTRL.get("active"):
        if now >= GREEN_CTRL["until"]:
            bot.stop()
            GREEN_CTRL["active"] = False
        return

    # No active rotation → compute command from latest centroid
    if centroid is None:
        bot.stop()
        return

    cx, cy = centroid
    err_x = cx - (config.FRAME_WIDTH // 2)
    angle_deg = _angle_deg_from_errx(err_x)

    # Deadband to avoid jitter
    if abs(angle_deg) <= config.GREEN_DEG_TOL:
        bot.stop()
        return

    # Choose speed (clamped)
    speed = clamp(
        GREEN_CTRL.get("speed", config.ROTATE_SPEED_DEFAULT),
        config.ROTATE_SPEED_MIN,
        config.ROTATE_SPEED_MAX,
    )

    # Compute duration from spin rate; cap for safety
    deg_per_sec = max(1e-6, config.SPIN_DEG_PER_SEC)
    duration = min(abs(angle_deg) / deg_per_sec, config.GREEN_MAX_DURATION_S) / 2

    # Direction: +angle => target right => rotate RIGHT (CW)
    # Our HAL: rotate_in_place(+speed) = CCW/left, (-speed) = CW/right
    signed_speed = -speed if angle_deg > 0 else +speed

    # Start timed spin and remember when to stop

    if angle_deg > 0:
        rotate_right(speed)
    else:
        rotate_left(speed)
    #rotate_left(speed)  # wrapper calls rotate_left/right under the hood
    time.sleep(duration)
    stop_robot()
    #GREEN_CTRL["active"] = True
    #GREEN_CTRL["until"] = now + duration
    #GREEN_CTRL["speed"] = speed  # keep for next calls (you can adaptively change it later)

def BlueAction(bot: Raspbot, p_vector):
    cx, cy = p_vector
    err_x = cx - (config.FRAME_WIDTH // 2)
    power = _bounded_power(-config.KP_STRAFE * err_x, config.POWER_MIN, config.POWER_MAX)
    print(f"[BlueAction] err_x={err_x} -> strafe power={power:.3f}")
    if power == 0:
        bot.stop()
    else:
        bot.strafe(power)

def RedAction(bot: Raspbot, centroid):
    print("Staring Red Action...")
    now = time.monotonic()

    cx, cy = centroid
    err_x = cx - (config.FRAME_WIDTH // 2)
    angle_deg = _angle_deg_from_errx(err_x)

    print("Angle Calculated: " + str(angle_deg))
    
    # Not active -> start the 180° spin once
    speed = clamp(
        config.ROTATE_SPEED_DEFAULT,
        config.ROTATE_SPEED_MIN,
        config.ROTATE_SPEED_MAX,
    )
    
    print("Speed Calculated: " + str(speed))
    
    try: 
        if angle_deg > 0:
            rotate_right(speed)
        else:
            rotate_left(speed)
        time.sleep(2)
        stop_robot()
    except KeyboardInterrupt:
        # 当用户按下停止时，停止小车运动功能 When the user presses the stop button, the car stops moving.
            stop_robot()
            print("off.")

# ---------------- Round-Robin Scheduler ----------------

def run():
    bot = Raspbot()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    try:
        StartupAction(bot)
        start_time = time.time()

        while True:
            if not TimerCheck(start_time):
                break

            ret, frame = cap.read()
            if not ret:
                print("[Camera] Frame grab failed; idling...")
                IdleAction(bot)
                time.sleep(config.TIME_SLICE_S)
                continue

            counts, masks = ColorCounter(frame)
            dom, p_vec = ColorLocator(counts, masks)

            GREEN_CTRL = {"active": False, "until": 2, "speed":config.ROTATE_SPEED_DEFAULT}
            
            if dom is None or p_vec is None:
                IdleAction(bot)
            elif dom == "green":
                GreenAction(bot, p_vec, GREEN_CTRL)
            elif dom == "blue":
                BlueAction(bot, p_vec)
            elif dom == "red":
                print("Calling Red Action...")
                RedAction(bot, p_vec)
            else:
                IdleAction(bot)

            time.sleep(config.TIME_SLICE_S)

    finally:
        bot.stop()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    run()
