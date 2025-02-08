import numpy as np
from collections import deque

class ObstacleAvoidance:
    def __init__(self, max_steering_angle=30, car_width=0.5, safety_margin=0.5):
        self.safe_distance = 2.0  # meters
        self.max_steering_angle = max_steering_angle
        self.car_width = car_width
        self.safety_margin = safety_margin
        self.obstacle_history = deque(maxlen=5)
        
        # Avoidance parameters
        self.steering_aggressiveness = 1.2
        self.deceleration_factor = 0.7
        self.lane_boundary_threshold = 0.8

    def adjust_steering(self, target_steering, obstacles, lane_info):
        if not obstacles:
            return target_steering, 1.0  # Return original steering and speed factor
        
        closest_obstacle = min(obstacles, key=lambda x: x['distance'])
        self.obstacle_history.append(closest_obstacle)
        
        if closest_obstacle['distance'] < self.safe_distance:
            adjusted_steering = self._calculate_avoidance(
                target_steering, 
                closest_obstacle,
                lane_info
            )
            speed_factor = self._calculate_speed_factor(closest_obstacle)
            return adjusted_steering, speed_factor
        
        return target_steering, 1.0

    def _calculate_avoidance(self, target_steering, obstacle, lane_info):
        # Calculate base avoidance direction
        obstacle_pos = obstacle['position']
        normalized_distance = max(0, (self.safe_distance - obstacle['distance']) / self.safe_distance)
        
        # Calculate avoidance vector
        avoid_direction = np.sign(-obstacle_pos)  # Steer away from obstacle
        avoidance_magnitude = self.steering_aggressiveness * normalized_distance
        
        # Calculate raw steering angle
        avoidance_steering = avoid_direction * self.max_steering_angle * avoidance_magnitude
        
        # Blend with target steering using weighted average
        blend_weight = min(1.0, normalized_distance * 2)  # More aggressive when closer
        blended_steering = (1 - blend_weight) * target_steering + blend_weight * avoidance_steering
        
        # Apply lane boundary constraints
        constrained_steering = self._apply_lane_constraints(blended_steering, lane_info)
        
        return constrained_steering

    def _calculate_speed_factor(self, obstacle):
        distance_ratio = obstacle['distance'] / self.safe_distance
        return max(0.2, min(1.0, distance_ratio ** self.deceleration_factor))

    def _apply_lane_constraints(self, steering, lane_info):
        if not lane_info:
            return steering
        
        # Get lane boundaries from vision system
        left_boundary = lane_info.get('left_boundary', -1.0)
        right_boundary = lane_info.get('right_boundary', 1.0)
        
        # Calculate predicted lateral position
        predicted_lateral = np.clip(steering / self.max_steering_angle, -1, 1)
        
        # Calculate safe boundaries with margin
        safe_left = left_boundary + self.car_width/2 + self.safety_margin
        safe_right = right_boundary - self.car_width/2 - self.safety_margin
        
        # Constrain steering if approaching boundaries
        if predicted_lateral < safe_left:
            overshoot = (safe_left - predicted_lateral) / self.lane_boundary_threshold
            steering += overshoot * self.max_steering_angle
        elif predicted_lateral > safe_right:
            overshoot = (predicted_lateral - safe_right) / self.lane_boundary_threshold
            steering -= overshoot * self.max_steering_angle
            
        return np.clip(steering, -self.max_steering_angle, self.max_steering_angle)

    def update_parameters(self, safe_distance=None, aggressiveness=None):
        if safe_distance:
            self.safe_distance = safe_distance
        if aggressiveness:
            self.steering_aggressiveness = aggressiveness