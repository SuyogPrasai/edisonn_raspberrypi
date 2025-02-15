from edison.components.road_traverser.Traverser import Traverser
from edison.components.vision_processor.vision_processor import VisualProcessor
from edison.components.obstacle_avoidance.ObstacleAvoider import ObstacleAvoidance
from edison.components.control.Control import EdisonCar
from edison._lib.point_navigator import PointNavigator
from edison.components.streaming_server.streamer import StreamManager
import threading


class MainController:
    def __init__(self):
        self.car = EdisonCar()
        self.point_navigator = PointNavigator(self.car)
        self.vision = VisualProcessor()
        # self.obstacle_avoid = ObstacleAvoidance()
        self.traverser = Traverser(self.car, self.point_navigator)

        self.streamer = StreamManager()
        self.streamer.start_stream()

        
    def run_loop(self):
        while True:
            # frame = self.vision.capture_frame()
            # self.streamer.update_frame(frame)
            
            self.traverser.turn_car(30)

            
            # Process vision data
            # obstacles = self.vision.detect_obstacles(frame)
            # lane_info = self.vision.detect_lanes(frame)
            
            # Calculate navigation
            # target_steering = self.traverser.calculate_steering()
            # adjusted_steering = self.obstacle_avoid.adjust_steering(
            #     target_steering, 
            #     obstacles,
            #     lane_info
            # )
            
            # Execute commands
            # self.car.set_steering(adjusted_steering)
            # self.car.set_speed(self.calculate_safe_speed(obstacles))
            
            # Update navigation
            # if self.traverser.reached_waypoint():
            #     self.traverser.next_waypoint()