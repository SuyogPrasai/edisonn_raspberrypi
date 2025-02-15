import numpy as np

frame_width = 1280
frame_height = 720
mtx = np.array([[1000, 0, frame_width / 2],  
                [0, 1000, frame_height / 2],  
                [0, 0, 1]], dtype=np.float32)

dist = np.zeros((1, 5), dtype=np.float32)

# Save to an absolute path (change "C:/temp/" or "/tmp/" as needed)
file_path = "camera_config.npz"  # Try a simple relative path first

try:
    np.savez(file_path, mtx=mtx, dist=dist, frame_width=frame_width, frame_height=frame_height)
    print(f"File saved successfully: {file_path}")
except Exception as e:
    print(f"Error saving file: {e}")
