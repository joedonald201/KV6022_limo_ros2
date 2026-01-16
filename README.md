# KV6022_LIMO_2526
A companion repo for the KV6022 Robotics and Automation module

For the workshop tasks, please refer to [wiki pages](https://github.com/kivrakh/KV6022_limo_ros2/wiki)

## Overview
An autonomous road inspection system using the AgileX LIMO robot to detect, localise, and quantify road potholes in a simulated environment.

## System Architecture

### Components
- **Detection Module**: HSV-based colour filtering for identifying pink potholes.
- **Localisation**: 3D position calculation using RGB-D camera depth and TF transforms.
- **Navigation Module**: Waypoint-based autonomous planning.
- **Visualisation Module**: Real-time RViz pose markers showing detected pothole locations.
- **Data Logging**: CSV and JSON export of pothole data.

### Software
- ROS2 Humble
- Gazebo
- Nav2 navigation stack
- OpenCV for image processing
- Python 3.10

## Installation

### Clone and Build
```bash
cd ~/KV6022_limo_ros2
git clone https://github.com/joedonald201/KV6022_limo_ros2.git
colcon build
source install/setup.bash
```

## How to Run

### Terminal 1: Gazebo
```bash
cd ~/KV6022_limo_ros2
source install/setup.bash
ros2 launch limo_gazebosim limo_gazebo_assessment.launch.py
```

### Terminal 2: Navigation Stack
```bash
cd ~/KV6022_limo_ros2
source install/setup.bash
ros2 launch KV6022_assessment limo_navigation.launch.py
```

### Terminal 3: Pothole Detector
```bash
cd ~/KV6022_limo_ros2
source install/setup.bash
python3 src/KV6022_assessment/KV6022_assessment/pothole_detector.py
```

### Terminal 4: Autonomous Navigation
```bash
cd ~/KV6022_limo_ros2
source install/setup.bash
```
Set the initial pose in RViz, then run:
```bash
ros2 run KV6022_assessment example_waypoint_follower
```

## System Operation

### Detection Algorithm
1. **Colour Filtering**: Converts BGR image to HSV colour space.
2. **Thresholding**: Isolates pink region (HSV range: 140-170, 50-255, 50-255).
3. **Contour Detection**: Identifies pothole boundaries.
4. **Area Calculation**: Calculates pothole size in pixels.
5. **Bounding Box**: Determines rectangular dimensions.

### Localisation Process
1. Obtains depth value at pothole centre from depth image.
2. Projects 2D image coordinates to 3D camera frame using camera intrinsics.
3. Transforms 3D point from camera frame to map frame using TF.
4. Publishes pose to `/object_location` topic.
5. Publishes markers to `/limo/object_markers` for RViz visualisation.

### Navigation Strategy
- **Waypoint-based follower**: Waypoints are generated around the track for robot to follow.
- **Coverage pattern**: Loop around the perimeter.

## Results

### Data Output

#### CSV File (`potholes.csv`)
Contains detected pothole data with columns:
- `id`: Unique detection identifier
- `map_x`: X coordinate in map frame (meters)
- `map_y`: Y coordinate in map frame (meters)
- `area`: Pothole area (pixels)
- `bbox_w`: Bounding box width (pixels)
- `bbox_h`: Bounding box height (pixels)

#### JSON File (`potholes.json`)
Structured data in JSON format with same information as CSV.

#### Visualisation
- **RViz**: Real-time RViz pose markers showing detected pothole locations
- **OpenCV Windows**: Real-time detection with contours and bounding boxes.
- **Terminal Output**: Live count and coordinates.

### Detection Parameters
```python
HSV_LOWER = (140, 50, 50)
HSV_UPPER = (170, 255, 255)
MIN_AREA = 100
```

### Camera Configuration
- **Topic**: `/limo_camera/image`
- **Depth Topic**: `/limo_camera/depth/image_raw`

### TF Frames
- **Global Frame**: `map`
- **Camera Frame**: `depth_link`
- **Robot Frame**: `base_footprint`

## Limitations

### Duplicate Detections
- Same pothole detected multiple times as robot passes by.
- Each camera frame generates a new detection.

### Localisation Dependency
- Requires manual 2D pose estimate in RViz after each Gazebo reset.

### Performance
- RViz can become unresponsive with 1000+ markers.

## Key Features
- Fully autonomous operation.
- Real-time pothole detection using computer vision.
- 3D localisation with depth camera integration.
- Map-based position reporting.
- Persistent data storage.
- Live visualisation in RViz.

## Author
- Joe Donald
- Student ID: 22024499
- Module: KV6022 Robotics & Automation
- Date: 16 Jan 2026
