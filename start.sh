#!/bin/bash
export DISPLAY=:0

# Ẩn con trỏ chuột
unclutter -idle 0 &

# Tắt screensaver
xset s off
xset -dpms
xset s noblank

# Chạy app fullscreen
cd /home/pi/Downloads/boxdata
python3 main.py
