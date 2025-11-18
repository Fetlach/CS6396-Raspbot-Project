CE 6308 — Project 1 Full Implementation (All Operations)

This version includes a fully implemented `robot.py` with two real backends:
1) GPIOZERO — EN (PWM) + IN1/IN2 per wheel using gpiozero + RPi.GPIO
2) PCA9685  — Adafruit PCA9685 for PWM + RPi.GPIO for direction

If neither library is detected, it falls back to a SIM backend that prints wheel speeds
so you can test on a laptop without hardware.

Quick Start
-----------
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Edit config.py:
- BACKEND = "GPIOZERO" or "PCA9685"
- Update pin maps for your wiring (BCM numbering)
- Tune HSV thresholds and controller gains

Run:
python main.py

Operations Implemented
----------------------
- StartupAction: ~360° spin (time-based) to signal ready
- TimerCheck: safety shutdown after MAX_RUNTIME_S
- ColorCounter: HSV color masks and pixel counts
- ColorLocator: dominant color + centroid
- IdleAction: stop motors
- GreenAction: rotate to center target horizontally
- BlueAction: strafe left/right to center target
- RedAction: ~180° rotation regardless of tracking status
- drive_forward/strafe/rotate_in_place: mapped via mecanum mixing
- spin_approx_degrees: time-based rotation helper

Notes
-----
- The mecanum mixer uses (vx, vy, wz) -> (FL, FR, RL, RR) with a standard sign convention.
- If one wheel is stronger/weaker, adjust WHEEL_SCALE in config.py.
- If your strafe direction is reversed, negate vy in rotate/strafe helpers or swap IN1/IN2 pins.

Safety
------
- Keep POWER_MIN low during first tests.
- Verify wheel directions with the SIM backend printouts before enabling motors.
