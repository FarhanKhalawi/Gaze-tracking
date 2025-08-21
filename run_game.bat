@echo off
cd Gaze_tracking_project

echo Installing required packages...
py -3.12 -m pip install -r requirements.txt

echo Running main.py (eye tracking demo)...
start py -3.12 main.py

timeout /t 1 >nul

echo Running gui_mediapip.py (eye-controlled game)...
start py -3.12 gui_mediapip.py

pause