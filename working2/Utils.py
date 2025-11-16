import time
import config
def current_milli_time():
    return round(time.time() * 1000)
def _angle_deg_from_errx(err_X: int) -> float:
    """
    Convert horizontal pixel error to approximate yaw angle (degrees).
    +angle => target is to the RIGHT of center (needs CW/right rotation).
    """

    half_w = config.FRAME_WIDTH / 2.0
    half_fov = config.CAMERA_HFOV_DEG / 2.0

    # err_x is positive when centroid is right of center
    return (err_x / half_w) * half_fov