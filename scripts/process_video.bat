@echo off
REM Usage: scripts\process_video.bat path\to\video.mp4
python src\video_pipeline.py "%~1"
