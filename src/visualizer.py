import cv2
import numpy as np
import config

class Visualizer:
    def __init__(self):
        pass

    def draw_counting_line(self, frame, p1=config.LINE_P1, p2=config.LINE_P2, is_flashing=False):
        color = config.COLOR_RED if is_flashing else config.COLOR_YELLOW
        thickness = 3 if is_flashing else 2

        cv2.line(frame, p1, p2, color, thickness)
        cv2.circle(frame, p1, 4, color, -1)
        cv2.circle(frame, p2, 4, color, -1)
        cv2.putText(frame, "COUNTING LINE", (p1[0] + 10, p1[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        return frame

    def draw_vehicles(self, frame, vehicles):
        for v_id, v in vehicles.items():
            x, y, w, h = v.bbox
            cx, cy = v.centroid

            # draw trail
            trail = list(v.trajectory)
            for i in range(1, len(trail)):
                cv2.line(frame, trail[i - 1], trail[i], config.COLOR_ORANGE, 2)

            # draw bbox and centroid
            box_color = config.COLOR_ORANGE if v.counted else config.COLOR_GREEN
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
            cv2.circle(frame, (cx, cy), 4, config.COLOR_RED, -1)

            # draw label
            label = f"ID:{v_id} | {v.speed:.1f}px/f"
            cv2.putText(frame, label, (x, max(15, y - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        return frame

    def draw_optical_flow(self, frame, prev_pts, curr_pts, scale=3.0):
        if len(prev_pts) == 0 or len(curr_pts) == 0:
            return frame

        for p0, p1 in zip(prev_pts, curr_pts):
            x0, y0 = int(p0[0]), int(p0[1])
            x1, y1 = int(p1[0]), int(p1[1])
            dx = int((x1 - x0) * scale)
            dy = int((y1 - y0) * scale)

            cv2.circle(frame, (x1, y1), 2, config.COLOR_CYAN, -1)
            if abs(dx) > 1 or abs(dy) > 1:
                cv2.arrowedLine(frame, (x0, y0), (x0 + dx, y0 + dy), (255, 0, 255), 1, tipLength=0.3)

        return frame

    def draw_hud(self, frame, fps, total_count, in_count, out_count, active_vehicles):
        h, w = frame.shape[:2]
        banner_h = 45

        # top banner
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, banner_h), (30, 30, 30), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        cv2.line(frame, (0, banner_h), (w, banner_h), config.COLOR_YELLOW, 2)

        # stats
        cv2.putText(frame, f"FPS: {fps:.1f}", (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128), 2)
        cv2.putText(frame, f"Active: {active_vehicles}", (140, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1)
        cv2.putText(frame, f"Total: {total_count}", (260, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, config.COLOR_YELLOW, 2)
        cv2.putText(frame, f"IN: {in_count} | OUT: {out_count}", (450, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1)

        return frame

    def draw_mask_thumbnail(self, frame, binary_mask):
        h, w = frame.shape[:2]
        thumb_w, thumb_h = 160, 90

        thumb = cv2.resize(binary_mask, (thumb_w, thumb_h))
        thumb_bgr = cv2.cvtColor(thumb, cv2.COLOR_GRAY2BGR)

        x_off = w - thumb_w - 10
        y_off = h - thumb_h - 10

        frame[y_off:y_off+thumb_h, x_off:x_off+thumb_w] = thumb_bgr
        cv2.rectangle(frame, (x_off, y_off), (x_off+thumb_w, y_off+thumb_h), (255, 255, 255), 1)
        cv2.putText(frame, "Mask", (x_off + 5, y_off + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

        return frame
