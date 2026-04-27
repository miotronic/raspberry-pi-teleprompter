#!/bin/bash
# Wait for KMS/DRM device to be ready
while [ ! -e /dev/dri/card0 ]; do sleep 1; done
while ! SDL_VIDEODRIVER=kmsdrm SDL_AUDIODRIVER=dummy SDL_VIDEO_KMSDRM_DEVICE=/dev/dri/card0 python3 -c "import pygame; pygame.display.init(); pygame.display.set_mode((800,480), pygame.FULLSCREEN); pygame.quit()" 2>/dev/null; do
    sleep 2
done

export SDL_VIDEODRIVER=kmsdrm
export SDL_AUDIODRIVER=dummy
export SDL_VIDEO_KMSDRM_DEVICE=/dev/dri/card0
exec python3 /home/zero/teleprompter/teleprompter.py >> /home/zero/teleprompter/start.log 2>&1
