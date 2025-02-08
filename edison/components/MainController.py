from edison.components.road_traverser import Traverser
from edison.components.vision_processor import VisionProcessor
from edison.components.obstacle_avoidance import ObstacleAvoidance
from edison.components.control.Control import EdisonCar
from edison._lib.point_navigator import PointNavigator

class MainController:
    def __init__(self):
        self.car = EdisonCar()
        self.vision = VisionProcessor()
        self.obstacle_avoid = ObstacleAvoidance()
        self.point_navigator = PointNavigator(self.car)
        self.traverser = Traverser(self.car, self.point_navigator)
        
    def run_loop(self):
        while True:
            # Get sensor data
            frame = self.vision.capture_frame()
            gps_data = self.car.get_location()
            
            # Process vision data
            obstacles = self.vision.detect_obstacles(frame)
            lane_info = self.vision.detect_lanes(frame)
            
            # Calculate navigation
            target_steering = self.traverser.calculate_steering()
            adjusted_steering = self.obstacle_avoid.adjust_steering(
                target_steering, 
                obstacles,
                lane_info
            )
            
            # Execute commands
            self.car.set_steering(adjusted_steering)
            self.car.set_speed(self.calculate_safe_speed(obstacles))
            
            # Update navigation
            if self.traverser.reached_waypoint():
                self.traverser.next_waypoint()