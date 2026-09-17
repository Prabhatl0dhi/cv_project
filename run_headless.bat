@echo off
cd /d "%~dp0"
call "%~dp0run.bat" --no-display --output-video output/annotated_traffic.mp4 %*
