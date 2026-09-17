from collections import deque
import cv2
import numpy as np
import config
from src.preprocessing import FramePreprocessor

class TrackedVehicle:
    def __init__(self, vehicle_id, bbox, centroid):
        self.vehicle_id = vehicle_id
        self.bbox = bbox
        self.centroid = centroid
        self.trajectory = deque(maxlen=30)
        self.trajectory.append(centroid)
        self.velocity = (0.0, 0.0)
        self.speed = 0.0
        self.total_distance = 0.0
        self.disappeared = 0
        self.counted = False
        self.direction = "UNKNOWN"

    def update(self, bbox, centroid):
        prev_x, prev_y = self.centroid
        new_x, new_y = centroid

        dx = float(new_x - prev_x)
        dy = float(new_y - prev_y)
        self.velocity = (dx, dy)
        self.speed = float(np.hypot(dx, dy))
        self.total_distance += self.speed

        self.bbox = bbox
        self.centroid = centroid
        self.trajectory.append(centroid)
        self.disappeared = 0

        # direction
        if len(self.trajectory) >= 3:
            start_y = self.trajectory[0][1]
            end_y = self.trajectory[-1][1]
            if end_y - start_y > 8:
                self.direction = "DOWN / OUT"
            elif start_y - end_y > 8:
                self.direction = "UP / IN"

class MotionSegmenter:
    def __init__(self, preprocessor=None):
        self.preprocessor = preprocessor if preprocessor else FramePreprocessor()
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=config.MOG2_HISTORY,
            varThreshold=config.MOG2_VAR_THRESHOLD,
            detectShadows=config.DETECT_SHADOWS
        )

    def get_foreground_mask(self, frame):
        raw_mask = self.bg_subtractor.apply(frame)
        cleaned_mask = self.preprocessor.clean_mask(raw_mask)
        return raw_mask, cleaned_mask

    def detect_vehicles(self, binary_mask):
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < config.MIN_CONTOUR_AREA or area > config.MAX_CONTOUR_AREA:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            if w < config.MIN_BBOX_WIDTH or h < config.MIN_BBOX_HEIGHT:
                continue

            aspect_ratio = float(w) / float(h) if h > 0 else 0
            if aspect_ratio < 0.2 or aspect_ratio > 4.5:
                continue

            # centroid from moments
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx = x + w // 2
                cy = y + h // 2

            detections.append(((x, y, w, h), (cx, cy), cnt))

        return detections

class KLTTracker:
    def __init__(self):
        self.feature_params = dict(
            maxCorners=config.KLT_MAX_CORNERS,
            qualityLevel=config.KLT_QUALITY,
            minDistance=config.KLT_MIN_DIST,
            blockSize=7
        )
        self.lk_params = dict(
            winSize=config.KLT_WIN_SIZE,
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )

    def get_features(self, gray_frame, bboxes):
        if not bboxes:
            return np.empty((0, 1, 2), dtype=np.float32)

        mask = np.zeros(gray_frame.shape, dtype=np.uint8)
        for (x, y, w, h) in bboxes:
            mask[y:y+h, x:x+w] = 255

        pts = cv2.goodFeaturesToTrack(gray_frame, mask=mask, **self.feature_params)
        if pts is None:
            return np.empty((0, 1, 2), dtype=np.float32)
        return pts

    def track_optical_flow(self, prev_gray, curr_gray, prev_pts):
        if prev_pts is None or len(prev_pts) == 0:
            return np.empty((0, 2)), np.empty((0, 2))

        curr_pts, status, _ = cv2.calcOpticalFlowPyrLK(
            prev_gray, curr_gray, prev_pts, None, **self.lk_params
        )

        if curr_pts is None or status is None:
            return np.empty((0, 2)), np.empty((0, 2))

        valid = (status.flatten() == 1)
        good_prev = prev_pts[valid].reshape(-1, 2)
        good_curr = curr_pts[valid].reshape(-1, 2)
        return good_prev, good_curr

class VehicleTracker:
    def __init__(self):
        self.next_id = 1
        self.vehicles = {}

    def register(self, bbox, centroid):
        self.vehicles[self.next_id] = TrackedVehicle(self.next_id, bbox, centroid)
        self.next_id += 1

    def deregister(self, vehicle_id):
        if vehicle_id in self.vehicles:
            del self.vehicles[vehicle_id]

    def update(self, detections):
        if len(detections) == 0:
            for v_id in list(self.vehicles.keys()):
                self.vehicles[v_id].disappeared += 1
                if self.vehicles[v_id].disappeared > config.MAX_DISAPPEARED:
                    self.deregister(v_id)
            return self.vehicles

        if len(self.vehicles) == 0:
            for bbox, centroid, _ in detections:
                self.register(bbox, centroid)
            return self.vehicles

        v_ids = list(self.vehicles.keys())
        existing_centroids = np.array([self.vehicles[i].centroid for i in v_ids])
        new_centroids = np.array([d[1] for d in detections])
        new_bboxes = [d[0] for d in detections]

        # distance matrix
        diff = existing_centroids[:, np.newaxis, :] - new_centroids[np.newaxis, :, :]
        dist_matrix = np.sqrt(np.sum(diff ** 2, axis=2))

        rows = dist_matrix.min(axis=1).argsort()
        cols = dist_matrix.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for r, c in zip(rows, cols):
            if r in used_rows or c in used_cols:
                continue

            if dist_matrix[r, c] > config.MAX_TRACK_DISTANCE:
                continue

            v_id = v_ids[r]
            self.vehicles[v_id].update(new_bboxes[c], tuple(new_centroids[c]))
            used_rows.add(r)
            used_cols.add(c)

        unused_rows = set(range(len(v_ids))).difference(used_rows)
        for r in unused_rows:
            v_id = v_ids[r]
            self.vehicles[v_id].disappeared += 1
            if self.vehicles[v_id].disappeared > config.MAX_DISAPPEARED:
                self.deregister(v_id)

        unused_cols = set(range(len(detections))).difference(used_cols)
        for c in unused_cols:
            self.register(new_bboxes[c], tuple(new_centroids[c]))

        return self.vehicles
