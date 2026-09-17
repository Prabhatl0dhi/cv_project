#!/usr/bin/env bash

cd "$(dirname "$0")" || exit 1

echo "========================================"
echo "      Traffic and Motion Analytics"
echo "========================================"
echo ""

PYTHON_CMD=""
if [ -f "venv/bin/activate" ]; then
    source "venv/bin/activate"
    PYTHON_CMD="python"
elif [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
    PYTHON_CMD="python"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python 3.8+."
    exit 1
fi

# check packages
"$PYTHON_CMD" -c "import cv2, numpy, pandas" &>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing requirements..."
    "$PYTHON_CMD" -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Failed to install requirements."
        exit 1
    fi
fi

HAS_INPUT=0
for arg in "$@"; do
    if [[ "$arg" == "--input" || "$arg" == "-i" ]]; then
        HAS_INPUT=1
        break
    fi
done

if [[ $# -gt 0 && "$1" != "--no-display" && "$1" != "--output-video" && "$1" != "-o" && "$1" != "--save-csv" && "$1" != "-c" ]]; then
    HAS_INPUT=1
fi

INPUT_ARGS=()

if [ $HAS_INPUT -eq 0 ]; then
    echo "Choose video source:"
    echo "  [1] sample_traffic.mp4 [Default]"
    echo "  [2] Sysvideo 4K 8 Megapixel  IP Camera Demo traffic car_2160p.mp4"
    echo "  [3] Live Webcam"
    echo "  [4] Custom video path / drag & drop"
    echo ""
    read -r -p "Select [1-4] (default 1): " CHOICE
    echo ""

    case "$CHOICE" in
        "1"|"")
            INPUT_ARGS=("--input" "sample_traffic.mp4")
            ;;
        "2")
            INPUT_ARGS=("--input" "Sysvideo 4K 8 Megapixel  IP Camera Demo traffic car_2160p.mp4")
            ;;
        "3")
            INPUT_ARGS=("--input" "0")
            ;;
        "4")
            read -r -p "Enter video path: " CUSTOM_PATH
            CUSTOM_PATH="${CUSTOM_PATH%\"}"
            CUSTOM_PATH="${CUSTOM_PATH#\"}"
            CUSTOM_PATH="${CUSTOM_PATH%\'}"
            CUSTOM_PATH="${CUSTOM_PATH#\'}"
            if [ -n "$CUSTOM_PATH" ]; then
                INPUT_ARGS=("--input" "$CUSTOM_PATH")
            else
                INPUT_ARGS=("--input" "sample_traffic.mp4")
            fi
            ;;
        *)
            CLEAN_CHOICE="${CHOICE%\"}"
            CLEAN_CHOICE="${CLEAN_CHOICE#\"}"
            INPUT_ARGS=("--input" "$CLEAN_CHOICE")
            ;;
    esac
fi

"$PYTHON_CMD" main.py "${INPUT_ARGS[@]}" "$@"
EXIT_CODE=$?

exit $EXIT_CODE
