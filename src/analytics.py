import os
import datetime
import pandas as pd
import config

class TrafficCounter:
    def __init__(self, line_p1=config.LINE_P1, line_p2=config.LINE_P2):
        self.p1 = line_p1
        self.p2 = line_p2
        self.total_count = 0
        self.in_count = 0
        self.out_count = 0
        self.records = []
        self.flash_line = 0

    def _is_ccw(self, a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

    def _segments_intersect(self, p1, q1, p2, q2):
        return (self._is_ccw(p1, p2, q2) != self._is_ccw(q1, p2, q2)) and \
               (self._is_ccw(p1, q1, p2) != self._is_ccw(p1, q1, q2))

    def check_crossing(self, vehicle):
        if vehicle.counted or len(vehicle.trajectory) < config.MIN_TRACK_FRAMES:
            return None

        if vehicle.total_distance < config.MIN_MOVEMENT_DIST:
            return None

        prev_pt = vehicle.trajectory[-2]
        curr_pt = vehicle.trajectory[-1]

        # check if trajectory crossed line
        if self._segments_intersect(prev_pt, curr_pt, self.p1, self.p2):
            vehicle.counted = True
            self.flash_line = 6

            dy = curr_pt[1] - prev_pt[1]
            dx = curr_pt[0] - prev_pt[0]

            if abs(dy) >= abs(dx):
                direction = "DOWN / OUT" if dy > 0 else "UP / IN"
            else:
                direction = "RIGHT / EAST" if dx > 0 else "LEFT / WEST"

            return direction

        return None

    def update(self, vehicles, frame_number):
        new_events = []

        for v in vehicles.values():
            direction = self.check_crossing(v)
            if direction:
                self.total_count += 1
                if "UP" in direction:
                    self.in_count += 1
                elif "DOWN" in direction:
                    self.out_count += 1

                record = {
                    "vehicle_id": v.vehicle_id,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "frame_number": frame_number,
                    "direction": direction,
                    "speed_px_frame": round(v.speed, 2),
                    "trajectory_length": len(v.trajectory)
                }
                self.records.append(record)
                new_events.append(record)

        if self.flash_line > 0:
            self.flash_line -= 1

        return new_events

    def export_csv(self, file_path=config.DEFAULT_CSV_PATH):
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        df = pd.DataFrame(self.records)
        if df.empty:
            df = pd.DataFrame(columns=[
                "vehicle_id", "timestamp", "frame_number", 
                "direction", "speed_px_frame", "trajectory_length"
            ])
        df.to_csv(file_path, index=False)
        return os.path.abspath(file_path)
