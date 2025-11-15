Real time systems project raspbot

These are the driver code files that make the robot rotate or move sideways based on the color the camera on the bot sees:

Task Function Description
StartupAction(): Runs once when the program first begins execution and is
never run again. The vehicle should spin in place for 360
degrees using the mecanum wheels to indicate that
initialization was successful. Once complete, begin the
round-robin execution loop.


TimerCheck(): For safety reasons, maintain a timer to track how long the
program has been executing. If the execution time is
greater than some threshold (i.e. 10 to 30 seconds) then
cease execution.


ColorCounter(image): Counts the number of pixels which match the command
colors. Returns a python dictionary, where the keys are the
command colors and the values are the associated counts.


ColorLocator(color_counts): Returns a 2D position vector to indicate the image location
of the command color object of whichever command color
has the largest number of pixels. For simplicity, you can
take the average position of all matching pixels. Utilize a
specific value to indicate an idle state when too few of a
command color’s pixels are detected.


IdleAction() :The vehicle should sit motionless when no command color
is detected.


GreenAction(p_vector): Rotate the vehicle in place using the mecanum wheels
until the horizontal component of the command color
object’s 2D position vector lies in the center of the camera
image. Do not rotate the camera’s gimbal – you must
rotate the vehicle’s body using the mecanum wheels.


BlueAction(p_vector): Move the vehicle sideways using the mecanum wheels
until the horizontal component of the command color
object’s 2D position vector lies in the center of the camera
image. Do not rotate the camera’s gimbal – you must
rotate the vehicle’s body using the mecanum wheels.


RedAction(): Rotate the vehicle 180 degrees such that it is looking away
from the command color object. Continue to rotate even
when the object is no longer seen on camera until the
vehicle has approximately rotated 180 degrees (some error
is fine).

