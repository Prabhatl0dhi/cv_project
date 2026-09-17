import cv2
import numpy as np
import config

class FramePreprocessor:
    def __init__(self):
        # clahe for lighting
        self.clahe = cv2.createCLAHE(
            clipLimit=config.CLAHE_CLIP_LIMIT,
            tileGridSize=config.CLAHE_GRID_SIZE
        )
        # kernels for noise removal
        self.kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, config.OPEN_KERNEL_SIZE)
        self.kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, config.CLOSE_KERNEL_SIZE)

    def resize_frame(self, frame, width=config.FRAME_WIDTH, height=config.FRAME_HEIGHT):
        if frame.shape[1] == width and frame.shape[0] == height:
            return frame
        return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

    def apply_clahe(self, frame):
        if not config.USE_CLAHE:
            return frame
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_eq = self.clahe.apply(l)
        merged = cv2.merge((l_eq, a, b))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    def smooth_frame(self, frame):
        return cv2.GaussianBlur(frame, config.GAUSSIAN_KERNEL, config.GAUSSIAN_SIGMA)

    def clean_mask(self, mask):
        # threshold shadow pixels
        _, binary = cv2.threshold(mask, 250, 255, cv2.THRESH_BINARY)
        # remove noise dots
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, self.kernel_open, iterations=config.OPEN_ITERATIONS)
        # fill vehicle holes
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, self.kernel_close, iterations=config.CLOSE_ITERATIONS)
        return closed

    def process_frame(self, frame):
        resized = self.resize_frame(frame)
        equalized = self.apply_clahe(resized)
        smoothed = self.smooth_frame(equalized)
        gray = cv2.cvtColor(smoothed, cv2.COLOR_BGR2GRAY)
        return smoothed, gray
