# Tunable parameters and constants for the RASPBOT RTOS project.

# Camera horizontal field of view (tune to your camera)
CAMERA_HFOV_DEG = 62.0

# Spin calibration (how fast your bot rotates at a given library "speed")
SPIN_DEG_PER_SEC = 120.0   # measure on your robot

# Rotation speed bounds used with the library (if it accepts a speed argument)
ROTATE_SPEED_MIN = 1
ROTATE_SPEED_MAX = 255
ROTATE_SPEED_DEFAULT = 100

# Angle tolerance: if computed yaw error is within this, don't rotate
GREEN_DEG_TOL = 2.0

# Safety cap (seconds) so a bad estimate never spins forever
GREEN_MAX_DURATION_S = 1.25

# Red
RED_DEGREES        = 180.0
# RED_SPEED_DEFAULT  = 100      # used if your library accepts a speed
RED_MAX_DURATION_S = 2.0       # safety cap
RED_DIRECTION      = "ccw"     # "ccw" or "cw"

# Safety: maximum program run time (seconds)
MAX_RUNTIME_S = 25

# Camera parameters
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Minimum pixels to consider a command "visible"
MIN_PIXELS_VISIBLE = 1200

# Vision: HSV thresholds for Green, Blue, Red (two ranges), tweak on hardware.
# Values are (H_low, S_low, V_low, H_high, S_high, V_high)
HSV_THRESHOLDS = {
    2: [(40, 70, 60, 85, 255, 255)], # green is 2
    3:  [(95, 80, 60, 135, 255, 255)], # blue is 3
    # Red wraps around HSV hue, so two ranges
    1:   [(0, 120, 70, 10, 255, 255), (170, 120, 70, 180, 255, 255)], #red is 1
}

RGB_THRESHOLDS = {
    "green": [(40, 100, 40, 120, 255, 120)],
    "blue":  [(40, 40, 120, 120, 120, 255)],
    "red":   [(120, 40, 40, 255, 120, 120)]
}

# Control gains (simple P controller to center horizontal error)
KP_ROTATE = 0.0035   # for GreenAction (rotate body to center x)
KP_STRAFE = 0.0040   # for BlueAction (strafe sideways to center x)

# Motor power limits [0..1]
POWER_MIN = 0.2
POWER_MAX = 0.8

# Startup spin parameters (approximate — calibrate on hardware)
SPIN_DEG_TARGET = 360        # degrees
SPIN_DEG_PER_SEC = 120       # your robot's spin rate at SPIN_POWER
SPIN_POWER = 0.4             # motor power during startup spin
SPIN_EXTRA_SAFETY = 0.3      # extra seconds to ensure full spin

# Round-robin time slice (seconds) per task
TIME_SLICE_S = 0.02  # ~50 Hz task cadence

# -------------------- Hardware Pin Map --------------------
# Choose one backend in BACKEND: 'GPIOZERO' or 'PCA9685'.
BACKEND = "GPIOZERO"  # change to 'PCA9685' if you have that wired

# If you use GPIOZERO (L298N/TB6612 per wheel: EN (PWM), IN1, IN2 on BCM numbering):
WHEELS_GPIOZERO = {
    # name: (EN_pwm_pin, IN1_pin, IN2_pin)
    "FL": (12, 5, 6),    # Front-Left  (example pins)
    "FR": (13, 20, 21),  # Front-Right
    "RL": (18, 22, 27),  # Rear-Left
    "RR": (19, 23, 24),  # Rear-Right
}
PWM_FREQUENCY_HZ = 1000

# If you use PCA9685 (e.g., TB6612 x2 with PCA9685 PWM and GPIO for direction):
PCA9685_I2C_ADDR = 0x40
PCA9685_FREQUENCY_HZ = 1000
# Map each wheel to (PWM_channel, IN1_gpio, IN2_gpio)
WHEELS_PCA9685 = {
    "FL": (0, 5, 6),
    "FR": (1, 20, 21),
    "RL": (2, 22, 27),
    "RR": (3, 23, 24),
}

# Mecanum geometry: sign conventions per wheel for strafe & rotate.
# These coefficients map desired body velocities (vx, vy, wz) to wheel speeds.
# vx: forward (+), vy: right strafe (+), wz: CCW rotation (+)
MECANUM_COEFFS = {
    "FL": (+1, -1, +1),
    "FR": (+1, +1, -1),
    "RL": (+1, +1, +1),
    "RR": (+1, -1, -1),
}

# Normalize factors for mixing (tweak if one wheel is stronger/weaker)
WHEEL_SCALE = {
    "FL": 1.0, "FR": 1.0, "RL": 1.0, "RR": 1.0,
}
