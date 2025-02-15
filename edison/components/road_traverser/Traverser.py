from edison.helpers.geoutils import haversine, calculate_bearing
from edison._lib.point_navigator import PointNavigator
from edison.components.control.Control import EdisonCar

from collections import deque
import numpy as np
import time

class Traverser:
    def __init__(self, car: EdisonCar, point_navigator: PointNavigator):
        self.car = car
        self.point_navigator = point_navigator
        self.counter = 0
        # self.next_point = self.point_navigator.routes[self.counter]
        
        # Lane keeping parameters
        self.lane_center = 0.0  # Normalized lane center position (-1 to 1)
        self.lane_curvature = 0.0  # Curvature in 1/meters
        self.lane_history = deque(maxlen=5)
        
        # PID controller for steering
        self.steering_pid = PIDController(Kp=0.8, Ki=0.01, Kd=0.05)
        self.last_update_time = time.time()

    def update_vision_data(self, lane_center, lane_curvature):
        """Called from vision system with latest lane data"""
        self.lane_center = lane_center
        self.lane_curvature = lane_curvature
        self.lane_history.append((lane_center, lane_curvature))

    def calculate_steering(self):
        base_angle = self.car._car_direction()
        lane_adjusted = self._adjust_for_curvature(base_angle)
        return self._limit_steering(lane_adjusted)

    def _adjust_for_curvature(self, base_angle):
        # Calculate needed steering from lane position
        lane_steering = self._calculate_lane_steering()
        
        # Predict future curvature
        curvature_compensation = self._calculate_curvature_compensation()
        
        # Combine waypoint and lane guidance
        combined_steering = self._fusion_steering(
            base_angle,
            lane_steering + curvature_compensation
        )
        
        return combined_steering

    def _calculate_lane_steering(self):
        """Calculate immediate steering correction based on lane center"""
        # Convert lane center (-1 to 1) to steering angle (-30 to 30 degrees)
        lane_offset = self.lane_center * self.car.max_steering_angle
        dt = time.time() - self.last_update_time
        
        # PID control
        steering_correction = self.steering_pid.update(lane_offset, dt)
        return steering_correction

    def _calculate_curvature_compensation(self):
        """Anticipate upcoming road curvature"""
        if len(self.lane_history) < 2:
            return 0
            
        # Calculate curvature trend
        curvatures = [c for _, c in self.lane_history]
        curvature_derivative = np.gradient(curvatures).mean()
        
        # Predict compensation (empirical factor)
        return self.car.speed * curvature_derivative * 0.12  # Tune this factor

    def _fusion_steering(self, waypoint_angle, lane_steering):
        """Sensor fusion: Combine waypoint and lane guidance"""
        # Weighting factors (adjust based on confidence)
        waypoint_weight = 0.6  # Higher when far from waypoints
        lane_weight = 0.4      # Higher when in clear lanes
        
        # Normalize angles
        wp_norm = waypoint_angle / self.car.max_steering_angle
        lane_norm = lane_steering / self.car.max_steering_angle
        
        # Weighted average
        combined = (waypoint_weight * wp_norm + lane_weight * lane_norm)
        return combined * self.car.max_steering_angle

    def _limit_steering(self, angle):
        """Ensure steering within vehicle limits"""
        return np.clip(angle, 
                      -self.car.max_steering_angle, 
                      self.car.max_steering_angle)

    def turn_car(self, direction: int) -> None:
        car_direction = self.car._car_direction()
        direction_change = direction - car_direction
        turning_speed = 50
        while True:
            if direction_change > 0: 
                self.car.turn_right()
                self.car.set_speed(turning_speed)
            elif direction_change < 0:
                self.car.turn_right()
                self.car.set_speed(turning_speed)
            else:
                self.car.turn_front()
                break
        time.sleep(3)
        self.car.set_speed(0)

class PIDController:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.reset()
        
    def reset(self):
        self.prev_error = 0
        self.integral = 0
        
    def update(self, error, dt):
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        self.prev_error = error
        return output