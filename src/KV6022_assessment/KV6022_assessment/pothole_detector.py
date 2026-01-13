#!/usr/bin/env python3
# Python libs
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy import qos
import math
import csv
import json

# OpenCV
import cv2

# ROS libraries
import image_geometry
from tf2_ros import Buffer, TransformListener
from tf2_geometry_msgs import do_transform_pose
from cv_bridge import CvBridge

# ROS Messages
from std_msgs.msg import Header
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import Pose, PoseStamped, Point, Quaternion

class PotholeDetector(Node):
    camera_model = None
    image_depth_ros = None
    color2depth_aspect = 1.0

    min_area_size = 100
    global_frame = 'map'
    visualisation = True

    def __init__(self):    
        super().__init__('pothole_detector')
        self.bridge = CvBridge()
        self.pothole_records = []
        self.pothole_count = 0
        self.csv_path = 'potholes.csv'
        self.json_path = 'potholes.json'

        self.camera_info_sub = self.create_subscription(CameraInfo, '/limo_camera/depth/camera_info', self.camera_info_callback, qos_profile=qos.qos_profile_sensor_data)
        self.image_sub = self.create_subscription(Image, '/limo_camera/image', self.image_color_callback, qos_profile=qos.qos_profile_sensor_data)
        self.image_sub = self.create_subscription(Image, '/limo_camera/depth/image_raw', self.image_depth_callback, qos_profile=qos.qos_profile_sensor_data)
        
        self.object_location_pub = self.create_publisher(PoseStamped, '/object_location', qos.qos_profile_parameters)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.camera_frame = 'depth_link'

    def camera_info_callback(self, data):
        if self.camera_model is None:
            self.camera_model = image_geometry.PinholeCameraModel()
            self.camera_model.fromCameraInfo(data)

    def image_depth_callback(self, data):
        self.image_depth_ros = data

    def image2camera_tf(self, image_coords, image_depth):
        depth_height, depth_width = image_depth.shape[:2]
        y, x = int(image_coords[0]), int(image_coords[1])
        
        if x < 0 or y < 0 or x >= depth_width or y >= depth_height:
            return None

        depth_value = image_depth[y, x]
        if depth_value <= 0.0 or np.isnan(depth_value):
            return None

        camera_coords = np.array(self.camera_model.projectPixelTo3dRay((image_coords[1], image_coords[0])))
        camera_coords /= camera_coords[2]
        camera_coords = camera_coords * depth_value
        
        pose = Pose(position=Point(x=camera_coords[0], y=camera_coords[1], z=camera_coords[2]), 
                    orientation=Quaternion(w=1.0))
        return pose

    def image_color_callback(self, data):
        if self.camera_model is None:
            return

        if self.image_depth_ros is None:
            return
        
        self.image_color = self.bridge.imgmsg_to_cv2(data, "bgr8")
        self.image_depth = self.bridge.imgmsg_to_cv2(self.image_depth_ros, "32FC1")
        
        hsv_img = cv2.cvtColor(self.image_color, cv2.COLOR_BGR2HSV)
        
        hsv_thresh = cv2.inRange(hsv_img,
                                 np.array((140, 50, 50)),
                                 np.array((170, 255, 255)))
        
        object_contours, hierachy = cv2.findContours(hsv_thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for num, cnt in enumerate(object_contours):
            area = cv2.contourArea(cnt)
            if area > self.min_area_size:
                bbox_x, bbox_y, bbox_w, bbox_h = cv2.boundingRect(cnt)

                cmoms = cv2.moments(cnt)
                if cmoms["m00"] == 0:
                    continue

                image_coords = (cmoms["m01"] / cmoms["m00"], cmoms["m10"] / cmoms["m00"])
                
                camera_pose = self.image2camera_tf(image_coords, self.image_depth)
                if camera_pose is None:
                    continue

                global_pose = do_transform_pose(camera_pose, 
                                                self.tf_buffer.lookup_transform(self.global_frame, self.camera_frame, rclpy.time.Time())) 

                self.object_location_pub.publish(PoseStamped(header=Header(frame_id=self.global_frame),
                                              pose=global_pose))        

                self.pothole_count += 1
                record = {
                    'id': self.pothole_count,
                    'map_x': float(global_pose.position.x),
                    'map_y': float(global_pose.position.y),
                    'area': float(area),
                    'bbox_w': int(bbox_w),
                    'bbox_h': int(bbox_h),
                }
                self.pothole_records.append(record)
                print(f'Total potholes detected: {self.pothole_count}')

                print(f'--- pothole {num} ---')
                print('image coords: ', image_coords)
                print('bounding box: ', bbox_x, bbox_y, bbox_w, bbox_h)
                print('area: ', area)
                print('camera coords: ', camera_pose.position)
                print('global coords: ', global_pose.position)

                if self.visualisation:
                    cv2.drawContours(self.image_color, [cnt], -1, (0, 0, 255), 2)
                    cv2.rectangle(self.image_color, (bbox_x, bbox_y), (bbox_x + bbox_w, bbox_y + bbox_h), (255, 0, 0), 2)
                    cv2.circle(self.image_color, (int(image_coords[1]), int(image_coords[0])), 5, (0, 255, 0), -1)

        if self.visualisation:
            self.image_depth *= 1.0/10.0
            self.image_color = cv2.resize(self.image_color, (0,0), fx=0.5, fy=0.5)
            self.image_depth = cv2.resize(self.image_depth, (0,0), fx=0.5, fy=0.5)
            cv2.imshow("image color", self.image_color)
            cv2.imshow("image depth", self.image_depth)
            cv2.waitKey(1)

    def save_results(self):
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'map_x', 'map_y', 'area', 'bbox_w', 'bbox_h'])
            for record in self.pothole_records:
                writer.writerow([
                    record['id'],
                    record['map_x'],
                    record['map_y'],
                    record['area'],
                    record['bbox_w'],
                    record['bbox_h'],
                ])

        with open(self.json_path, 'w') as f:
            json.dump(self.pothole_records, f, indent=2)
            

def main(args=None):
    rclpy.init(args=args)
    image_projection = PotholeDetector()
    try:
        rclpy.spin(image_projection)
    except KeyboardInterrupt:
        pass
    finally:
        image_projection.save_results()
        image_projection.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

    
