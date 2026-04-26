#!/bin/bash
export SDL_VIDEODRIVER=kmsdrm
export SDL_AUDIODRIVER=dummy
exec python3 /home/pi/teleprompter/teleprompter.py >> /home/pi/teleprompter/start.log 2>&1
