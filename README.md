# Intelligent Traffic & Motion Analytics (Classical Computer Vision)

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Computer Vision](https://img.shields.io/badge/Domain-Computer%20Vision-success.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CLI Executable](https://img.shields.io/badge/CLI-Headless%20%26%20GUI-orange.svg)](#execution-modes)

A high-performance, modular Computer Vision system built for real-time traffic monitoring, vehicle motion segmentation, multi-object centroid tracking, Lucas-Kanade optical flow motion vector calculation, and virtual tripwire directional counting — implemented strictly using **classical computer vision algorithms** without heavy deep learning framework dependencies.

---

## 📋 Table of Contents
- [Project Highlights & Syllabus Alignment](#-project-highlights--syllabus-alignment)
- [System Architecture](#-system-architecture)
- [Prerequisites & Environment Setup](#-prerequisites--environment-setup)
- [Step-by-Step Installation](#-step-by-step-installation)
- [Execution Modes & CLI Guide](#-execution-modes--cli-guide)
- [Command-Line Arguments Reference](#-command-line-arguments-reference)
- [Interactive Controls (GUI Mode)](#-interactive-controls-gui-mode)
- [Project Directory Structure](#-project-directory-structure)
- [Telemetry & CSV Output](#-telemetry--csv-output)
- [Project Reports (.docx & .md)](#-project-reports-docx--md)
- [Evaluation & Submission Checklist](#-evaluation--submission-checklist)

---

## 🎯 Project Highlights & Syllabus Alignment

This project is mapped directly to standard **Computer Vision** academic course modules:

| Curriculum Module | Implemented Techniques & Algorithms | Source File |
| :--- | :--- | :--- |
| **Module 1: Image Preprocessing** | Spatial Gaussian filtering ($\sigma=1.5$), LAB color space splitting, and Contrast Limited Adaptive Histogram Equalization (CLAHE) for illumination normalization. | [`src/preprocessing.py`](src/preprocessing.py) |
| **Module 2: Motion Analysis** | Adaptive Mixture of Gaussians (MOG2) background subtraction with dynamic shadow suppression and morphological kernel filtering (Opening & Closing). | [`src/motion_tracker.py`](src/motion_tracker.py) |
| **Module 3: Feature Detection & Optical Flow** | Shi-Tomasi corner extraction (*Good Features to Track*) within candidate vehicle bounding boxes and pyramidal Lucas-Kanade (KLT) sparse motion vectors. | [`src/motion_tracker.py`](src/motion_tracker.py) |
| **Module 4: Multi-Object Tracking & Analytics** | Minimum Euclidean distance centroid association, track life-cycle management (`MAX_DISAPPEARED=15`), and vector cross-product virtual tripwire line intersection for directional counting. | [`src/motion_tracker.py`](src/motion_tracker.py)<br>[`src/analytics.py`](src/analytics.py) |

---

## 🏗️ System Architecture

```
                       [ Input Video / Webcam Feed ]
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │              1. Frame Preprocessing                    │
        │  • Resize (960x540)  • CLAHE (L-channel)  • Blur (7x7) │
        └────────────────────────────┬───────────────────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │              2. Motion Segmentation (MOG2)             │
        │  • Background Subtraction  • Shadow Removal (>250)     │
        │  • Morphological Opening (5x5) & Closing (9x9)         │
        │  • Contour Detection & Area Filtering (1800 - 80000)   │
        └────────────────────────────┬───────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
        ┌───────────────────────┐         ┌───────────────────────┐
        │ 3. Centroid Tracker   │         │ 4. Lucas-Kanade (KLT) │
        │ • Euclidean Matching  │         │ • Shi-Tomasi Corners  │
        │ • ID Assignment       │         │ • Motion Vectors      │
        │ • Trajectory History  │         │ • Velocity Estimation │
        └───────────┬───────────┘         └───────────┬───────────┘
                    │                                 │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │            5. Virtual Tripwire & Analytics             │
        │  • 2D Segment Intersection Test (CCW Orientation)      │
        │  • Directional Counting (IN/Up vs OUT/Down)            │
        │  • Real-time Telemetry & Time-stamped CSV Export       │
        └────────────────────────────┬───────────────────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │                 6. Visual HUD & Output                 │
        │  • Bounding Boxes, ID Tags, Breadcrumb Trails          │
        │  • Live FPS & Counts HUD  • Mask Picture-in-Picture    │
        │  • Optional Headless Mode & Annotated Video Export     │
        └────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start: 1-Click Direct Launchers (.bat & .sh)

The repository provides zero-configuration, automated launch scripts that detect your Python environment, auto-activate virtual environments, verify dependencies, prompt you to select or drag-and-drop your video file, and run the pipeline instantly.

### 🎛️ Interactive Video Selection Menu
When you run `run.bat` (or `./run.sh`) without arguments or by double-clicking, an interactive menu allows you to choose your video source with one keypress:

```text
-----------------------------------------------------------------
 Choose Video Input Source:
-----------------------------------------------------------------
  [1] sample_traffic.mp4 (Default)
  [2] Sysvideo 4K 8 Megapixel  IP Camera Demo traffic car_2160p.mp4
  [3] Live Webcam (0)
  [4] Custom path or drag and drop video
-----------------------------------------------------------------
Select [1-4] (default 1):
```

### 🪟 On Windows (Command Prompt / PowerShell / File Explorer)
- **Direct Launch with Video Selection Menu (Double-click or CLI):**
  ```cmd
  run.bat
  ```
- **Direct Headless Run (Generates annotated video & CSV):**
  ```cmd
  run_headless.bat
  ```
- **Run with Specific Video directly (Positional or Flagged):**
  ```cmd
  run.bat "Sysvideo 4K 8 Megapixel  IP Camera Demo traffic car_2160p.mp4"
  # Or
  run.bat --input "sample_traffic.mp4" --save-csv "output/traffic_analytics_report.csv"
  ```

### 🐧 On Linux & macOS (Terminal)
- **Direct Launch with Video Selection Menu:**
  ```bash
  chmod +x run.sh run_headless.sh
  ./run.sh
  ```
- **Direct Headless Run:**
  ```bash
  ./run_headless.sh
  ```
- **Run with Specific Video directly:**
  ```bash
  ./run.sh "Sysvideo 4K 8 Megapixel  IP Camera Demo traffic car_2160p.mp4"
  # Or
  ./run.sh --input "sample_traffic.mp4" --output-video output/result.mp4
  ```

---

## 💻 Prerequisites & Environment Setup

- **Python Version:** Python 3.8, 3.9, 3.10, 3.11, 3.12, or 3.13
- **Operating System:** Windows, macOS, or Linux
- **Terminal Shell:** PowerShell, Command Prompt, or Bash

---

## 📦 Step-by-Step Manual Installation

### 1. Clone the Public Repository
```bash
git clone https://github.com/prabhatl0dhi/cv_project.git
cd cv_project
```

### 2. Create and Activate a Virtual Environment
- **On Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **On Windows (Command Prompt):**
  ```cmd
  python -m venv venv
  venv\Scripts\activate.bat
  ```
- **On Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Execution Modes & CLI Guide

The project is **100% executable from the command line** with both headless (server-friendly) and interactive desktop GUI modes. You can run via the direct scripts (`run.bat` / `./run.sh`) or directly using `python main.py`.

### 1. Headless Execution 
Runs the entire pipeline in the terminal without opening a GUI window, generates the annotated result video, and exports telemetry to CSV:
```bash
# Windows
run.bat --no-display --output-video output/annotated_traffic.mp4
# Or direct Python
python main.py --no-display --output-video output/annotated_traffic.mp4
```

### 2. Interactive GUI Mode 
Runs with full visual overlays, picture-in-picture mask thumbnail, and real-time HUD:
```bash
# Windows
run.bat
# Linux / macOS
./run.sh
# Or direct Python
python main.py
```

### 3. Run with a Custom Video File
```bash
run.bat --input "sample_traffic.mp4" --save-csv "output/traffic_analytics_report.csv"
```


### 4. Run with Live Connected Webcam
```bash
run.bat --input 0
```

---

## ⚙️ Command-Line Arguments Reference

| Argument | Short | Type | Default | Description |
| :--- | :---: | :---: | :--- | :--- |
| `--input` | `-i` | `str` / `list` | `sample_traffic.mp4` | Path to video file or camera index (e.g. `0` for webcam). |
| `--output-video` | `-o` | `str` | `None` | Optional path to record and save annotated video (e.g. `output/result.mp4`). |
| `--save-csv` | `-c` | `str` | `output/traffic_analytics_report.csv` | Output file path for CSV telemetry logs. |
| `--no-display` | - | `flag` | `False` | Run headlessly without opening an OpenCV GUI window (ideal for CLI evaluation). |

---

## 🎮 Interactive Controls (GUI Mode)

When running in GUI mode, the following keyboard controls are active:

| Key | Action |
| :---: | :--- |
| <kbd>Q</kbd> or <kbd>Esc</kbd> | Quit and exit the pipeline (automatically saves CSV telemetry). |
| <kbd>P</kbd> | Pause / Resume the video playback. |
| <kbd>M</kbd> | Toggle the picture-in-picture Foreground Mask thumbnail (on/off). |
| <kbd>S</kbd> | Save a high-resolution screenshot of the current frame (`screenshot_frame_X.jpg`). |

---

## 📁 Project Directory Structure

```
cv_project/
├── src/
│   ├── __init__.py           
│   ├── preprocessing.py       
│   ├── motion_tracker.py      
│   ├── analytics.py           
│   └── visualizer.py          
├── output/
│   ├── .gitkeep                      
│   ├── traffic_analytics_report.csv  
│   └── annotated_traffic.mp4         
├── .gitignore                
├── config.py                  
├── main.py                    
├── run.bat                    
├── run.sh                     
├── run_headless.bat           
├── run_headless.sh            
├── sample_traffic.mp4         
├── Sysvideo 4K 8 Megapixel  IP Camera Demo traffic car_2160p.mp4  
├── PROJECT_REPORT.docx        
├── PROJECT_REPORT.md          
├── requirements.txt       
└── README.md                 

---

## 📊 Telemetry & CSV Output

Upon completing execution (or pressing `Q`), summary metrics are printed to the terminal and time-stamped telemetry is written to `output/traffic_analytics_report.csv`:

```
==========================================
         TRAFFIC ANALYTICS SUMMARY        
==========================================
  Total Vehicles Counted : 13
  Inbound (Up)           : 6
  Outbound (Down)        : 7
  CSV Report Saved To    : output/traffic_analytics_report.csv
==========================================
```

### Sample CSV Log Format
```csv
vehicle_id,timestamp,frame_number,direction,speed_px_frame,trajectory_length
1,2026-09-17 10:47:32,60,DOWN / OUT,5.0,28
2,2026-09-17 10:47:32,60,UP / IN,7.21,29
3,2026-09-17 10:47:34,113,DOWN / OUT,3.0,22
7,2026-09-17 10:47:35,125,DOWN / OUT,3.16,25
5,2026-09-17 10:47:35,129,UP / IN,4.0,27
```

---



