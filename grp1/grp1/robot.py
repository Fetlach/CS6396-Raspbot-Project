# Fully implemented hardware abstraction for a RASPBOT-style mecanum robot.
# Supports two backends:
#   - GPIOZERO: uses gpiozero + RPi.GPIO for PWM + direction pins (per wheel)
#   - PCA9685 : uses Adafruit_PCA9685 for PWM and RPi.GPIO for direction pins
#
# If neither backend is available, falls back to a simulator that prints actions.
#
# Operations provided:
#   stop()
#   drive_forward(power)
#   strafe(power)                 # right (+), left (-)
#   rotate_in_place(power)        # CCW (+), CW (-)
#   spin_approx_degrees(deg, power, deg_per_sec)
#   sleep(seconds)

import time
import math
from typing import Dict, Tuple
import config

# --------------- Utility ---------------

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def deadband(x, eps=1e-6):
    return 0.0 if abs(x) < eps else x

# --------------- Backends ---------------

class _BaseBackend:
    def __init__(self):
        self.names = ["FL", "FR", "RL", "RR"]
    def set_wheel(self, name: str, speed: float):
        raise NotImplementedError
    def stop_all(self):
        for n in self.names:
            self.set_wheel(n, 0.0)
    def close(self):
        pass

class _GPIOZeroBackend(_BaseBackend):
    def __init__(self):
        super().__init__()
        try:
            from gpiozero import PWMOutputDevice, DigitalOutputDevice
            import RPi.GPIO as GPIO  # noqa: F401
        except Exception as e:
            raise RuntimeError("GPIOZERO backend not available: %s" % e)

        self.PWMOutputDevice = PWMOutputDevice
        self.DigitalOutputDevice = DigitalOutputDevice
        self.pwm_freq = getattr(config, "PWM_FREQUENCY_HZ", 1000)

        self._wheels = {}
        for name, (en, in1, in2) in config.WHEELS_GPIOZERO.items():
            pwm = PWMOutputDevice(en, frequency=self.pwm_freq, initial_value=0.0)
            d1  = DigitalOutputDevice(in1, active_high=True, initial_value=False)
            d2  = DigitalOutputDevice(in2, active_high=True, initial_value=False)
            self._wheels[name] = (pwm, d1, d2)

    def set_wheel(self, name: str, speed: float):
        # speed in [-1,1], map to direction pins + PWM duty
        speed = clamp(speed, -1.0, 1.0)
        pwm, d1, d2 = self._wheels[name]
        if speed >= 0:
            d1.on(); d2.off()
            pwm.value = speed
        else:
            d1.off(); d2.on()
            pwm.value = -speed

    def close(self):
        for pwm, d1, d2 in self._wheels.values():
            pwm.value = 0.0
            d1.off(); d2.off()

class _PCA9685Backend(_BaseBackend):
    def __init__(self):
        super().__init__()
        try:
            from Adafruit_PCA9685 import PCA9685
            from gpiozero import DigitalOutputDevice
        except Exception as e:
            raise RuntimeError("PCA9685 backend not available: %s" % e)

        self.PCA9685 = PCA9685
        self.DigitalOutputDevice = DigitalOutputDevice

        self.pwm = self.PCA9685(address=config.PCA9685_I2C_ADDR)
        self.pwm.set_pwm_freq(config.PCA9685_FREQUENCY_HZ)

        self._wheels = {}
        for name, (ch, in1, in2) in config.WHEELS_PCA9685.items():
            d1  = self.DigitalOutputDevice(in1, active_high=True, initial_value=False)
            d2  = self.DigitalOutputDevice(in2, active_high=True, initial_value=False)
            self._wheels[name] = (ch, d1, d2)

    def _set_pwm(self, channel: int, duty: float):
        # duty in [0,1]; PCA9685 expects 12-bit 0..4095
        duty = clamp(duty, 0.0, 1.0)
        on = 0
        off = int(4095 * duty)
        self.pwm.set_pwm(channel, on, off)

    def set_wheel(self, name: str, speed: float):
        speed = clamp(speed, -1.0, 1.0)
        ch, d1, d2 = self._wheels[name]
        if speed >= 0:
            d1.on(); d2.off()
            self._set_pwm(ch, speed)
        else:
            d1.off(); d2.on()
            self._set_pwm(ch, -speed)

    def close(self):
        for ch, d1, d2 in self._wheels.values():
            self._set_pwm(ch, 0.0)
            d1.off(); d2.off()

class _SimBackend(_BaseBackend):
    def __init__(self):
        super().__init__()
        print("[SIM] Using simulator backend (no GPIO libraries found).")
        self._speeds = {n: 0.0 for n in self.names}
    def set_wheel(self, name: str, speed: float):
        self._speeds[name] = clamp(speed, -1.0, 1.0)
        print(f"[SIM] {name} -> {self._speeds[name]:+.2f}")
    def stop_all(self):
        for n in self.names:
            self._speeds[n] = 0.0
        print("[SIM] stop_all()")

# --------------- High-Level Robot ---------------

class Raspbot:
    def __init__(self):
        # Pick backend per config and availability
        backend = None
        prefer = getattr(config, "BACKEND", "GPIOZERO").upper()
        if prefer == "GPIOZERO":
            try:
                backend = _GPIOZeroBackend()
            except Exception as e:
                print("[Raspbot] GPIOZERO backend unavailable:", e)
        if backend is None and prefer == "PCA9685" or backend is None:
            try:
                backend = _PCA9685Backend()
            except Exception as e:
                print("[Raspbot] PCA9685 backend unavailable:", e)
        if backend is None:
            backend = _SimBackend()

        self.backend = backend
        self.coeffs = config.MECANUM_COEFFS
        self.scale  = config.WHEEL_SCALE

        # Current commanded wheel speeds (for optional telemetry)
        self._last_cmd = {n:0.0 for n in ["FL","FR","RL","RR"]}

    # ---- Low-level wheel write ----
    def _apply_wheels(self, speeds: Dict[str, float]):
        for name, sp in speeds.items():
            sp = clamp(sp * self.scale.get(name, 1.0), -1.0, 1.0)
            self.backend.set_wheel(name, sp)
            self._last_cmd[name] = sp

    # ---- Mix body velocities into wheel speeds ----
    # vx: forward (+), vy: right strafe (+), wz: CCW rotate (+)
    def _mix(self, vx: float, vy: float, wz: float) -> Dict[str, float]:
        # Raw mix
        raw = {}
        maxmag = 1e-9
        for n, (ax, ay, az) in self.coeffs.items():
            s = ax*vx + ay*vy + az*wz
            raw[n] = s
            maxmag = max(maxmag, abs(s))
        # Normalize if any exceeds 1.0
        if maxmag > 1.0:
            for n in raw:
                raw[n] /= maxmag
        return raw

    # ---- Public high-level operations ----
    def stop(self):
        self.backend.stop_all()

    def drive_forward(self, power: float):
        power = clamp(power, -1.0, 1.0)
        speeds = self._mix(vx=power, vy=0.0, wz=0.0)
        self._apply_wheels(speeds)

    def strafe(self, power: float):
        power = clamp(power, -1.0, 1.0)
        speeds = self._mix(vx=0.0, vy=power, wz=0.0)
        self._apply_wheels(speeds)

    def rotate_in_place(self, power: float):
        power = clamp(power, -1.0, 1.0)
        speeds = self._mix(vx=0.0, vy=0.0, wz=power)
        self._apply_wheels(speeds)

    def sleep(self, seconds: float):
        time.sleep(seconds)

    def spin_approx_degrees(self, degrees: float, power: float, deg_per_sec: float):
        # positive degrees -> CCW; negative -> CW
        power = clamp(power, 0.0, 1.0)
        if deg_per_sec <= 0:
            return
        dur = abs(degrees) / deg_per_sec
        signed = power if degrees >= 0 else -power
        self.rotate_in_place(signed)
        self.sleep(dur)
        self.stop()
    
    def _angle_deg_from_errx(err_x: int) -> float:
        """
        Convert horizontal pixel error to approximate yaw angle (degrees).
        +angle => target is to the RIGHT of center (needs CW/right rotation).
        """
        half_w = config.FRAME_WIDTH / 2.0
        half_fov = config.CAMERA_HFOV_DEG / 2.0
        # err_x is positive when centroid is right of center
        return (err_x / half_w) * half_fov
    
    def clamp(x, lo, hi):
        return lo if x < lo else hi if x > hi else x