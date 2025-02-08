# Navigation
WAYPOINT_THRESHOLD = 5  # meters
MAX_STEERING_ANGLE = 30  # degrees

# Vision
YOLO_CONF_THRESH = 0.5
LANE_DETECTION_CONFIG = {
    'canny_thresh1': 50,
    'canny_thresh2': 150,
    'hough_thresh': 50
}

# Safety
MINIMUM_DISTANCE = 1.5  # meters
EMERGENCY_STOP_SPEED = 0  # km/h

# Priority levels (higher = more important)
PRIORITIES = {
    'emergency_stop': 3,
    'obstacle_avoidance': 2,
    'lane_keeping': 1,
    'waypoint_navigation': 0
}