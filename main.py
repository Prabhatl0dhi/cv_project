import sys
import os
import time
import argparse
import cv2
import numpy as np

import config
from src.preprocessing import FramePreprocessor
from src.motion_tracker import MotionSegmenter, KLTTracker, VehicleTracker
from src.analytics import TrafficCounter
from src.visualizer import Visualizer

def run_pipeline(video_path, output_video=None, csv_output=config.DEFAULT_CSV_PATH, display=True):
    video_path = str(video_path).strip()
    if (video_path.startswith('"') and video_path.endswith('"')) or (video_path.startswith("'") and video_path.endswith("'")):
        video_path = video_path[1:-1].strip()

    # open video or webcam
    if video_path.isdigit():
        print(f"Connecting to webcam {video_path}...")
        cap = cv2.VideoCapture(int(video_path))
    else:
        resolved_path = video_path
        if not os.path.isfile(resolved_path):
            norm = "".join(video_path.lower().split())
            for f in os.listdir("."):
                if f.endswith((".mp4", ".avi", ".mov", ".mkv")) and "".join(f.lower().split()) == norm:
                    resolved_path = f
                    break

        if not os.path.isfile(resolved_path):
            print(f"Error: Video file not found -> {video_path}")
            return

        print(f"Opening video: {resolved_path}")
        cap = cv2.VideoCapture(resolved_path)

    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    # initialize modules
    preprocessor = FramePreprocessor()
    segmenter = MotionSegmenter(preprocessor)
    klt_tracker = KLTTracker()
    tracker = VehicleTracker()
    counter = TrafficCounter()
    visualizer = Visualizer()

    writer = None
    if output_video:
        os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)
        fps_in = cap.get(cv2.CAP_PROP_FPS) or 30.0
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_video, fourcc, fps_in, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
        print(f"Saving output video to: {output_video}")

    window_name = "Traffic Analytics"
    if display:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    print("Running... (Press 'q' to quit, 'p' to pause, 'm' for mask, 's' for screenshot)")

    frame_num = 0
    fps = 0.0
    prev_gray = None
    show_mask = True
    paused = False

    try:
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    print("End of video.")
                    break

                frame_num += 1
                t0 = time.time()

                # 1. preprocess frame
                proc_bgr, proc_gray = preprocessor.process_frame(frame)

                # 2. background subtraction and vehicle detection
                _, clean_mask = segmenter.get_foreground_mask(proc_bgr)
                detections = segmenter.detect_vehicles(clean_mask)

                # 3. tracking
                active_vehicles = tracker.update(detections)

                # 4. optical flow
                prev_pts, curr_pts = np.empty((0, 2)), np.empty((0, 2))
                if prev_gray is not None:
                    bboxes = [v.bbox for v in active_vehicles.values()]
                    corners = klt_tracker.get_features(prev_gray, bboxes)
                    if len(corners) > 0:
                        prev_pts, curr_pts = klt_tracker.track_optical_flow(prev_gray, proc_gray, corners)

                prev_gray = proc_gray.copy()

                # 5. count line crossing
                new_events = counter.update(active_vehicles, frame_num)
                for e in new_events:
                    print(f"Frame {e['frame_number']} | Car #{e['vehicle_id']} -> {e['direction']} | Speed: {e['speed_px_frame']} px/f")

                # calculate fps
                dt = time.time() - t0
                fps = 0.9 * fps + 0.1 * (1.0 / max(dt, 0.001))

                # 6. draw overlays
                vis_frame = proc_bgr.copy()
                vis_frame = visualizer.draw_vehicles(vis_frame, active_vehicles)
                vis_frame = visualizer.draw_optical_flow(vis_frame, prev_pts, curr_pts)
                vis_frame = visualizer.draw_counting_line(vis_frame, is_flashing=(counter.flash_line > 0))
                vis_frame = visualizer.draw_hud(vis_frame, fps, counter.total_count, counter.in_count, counter.out_count, len(active_vehicles))

                if show_mask:
                    vis_frame = visualizer.draw_mask_thumbnail(vis_frame, clean_mask)

                if writer is not None:
                    writer.write(vis_frame)

            if display:
                cv2.imshow(window_name, vis_frame)
                key = cv2.waitKey(1) & 0xFF

                if key in [ord('q'), ord('Q'), 27]:
                    print("Stopped by user.")
                    break
                elif key in [ord('p'), ord('P')]:
                    paused = not paused
                    print("Paused" if paused else "Resumed")
                elif key in [ord('m'), ord('M')]:
                    show_mask = not show_mask
                elif key in [ord('s'), ord('S')]:
                    snap = f"screenshot_{frame_num}.jpg"
                    cv2.imwrite(snap, vis_frame)
                    print(f"Saved: {snap}")

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        cap.release()
        if writer is not None:
            writer.release()
        if display:
            cv2.destroyAllWindows()

        csv_file = counter.export_csv(csv_output)
        print("\n--- Summary ---")
        print(f"Total counted: {counter.total_count}")
        print(f"Inbound (Up): {counter.in_count}")
        print(f"Outbound (Down): {counter.out_count}")
        print(f"CSV saved to: {csv_file}\n")

def main():
    parser = argparse.ArgumentParser(description="Traffic Analytics")
    parser.add_argument("positional_input", nargs="*", default=[], help="Video file or camera index")
    parser.add_argument("--input", "-i", nargs="*", default=None, help="Video file path")
    parser.add_argument("--output-video", "-o", type=str, default=None, help="Save video path")
    parser.add_argument("--save-csv", "-c", type=str, default=config.DEFAULT_CSV_PATH, help="CSV output path")
    parser.add_argument("--no-display", action="store_true", help="Run without GUI")

    args = parser.parse_args()

    if args.input is not None and len(args.input) > 0:
        raw_input = args.input
    elif len(args.positional_input) > 0:
        raw_input = args.positional_input
    else:
        raw_input = ["sample_traffic.mp4"]

    if isinstance(raw_input, list):
        video_source = " ".join(raw_input) if len(raw_input) > 0 else "sample_traffic.mp4"
    else:
        video_source = str(raw_input)

    run_pipeline(
        video_path=video_source,
        output_video=args.output_video,
        csv_output=args.save_csv,
        display=not args.no_display
    )

if __name__ == "__main__":
    main()
