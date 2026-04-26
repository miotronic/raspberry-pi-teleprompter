# RPi Zero Teleprompter

A lightweight, dedicated teleprompter built on a Raspberry Pi Zero 2 W, running a custom Python/Pygame application. Designed to be cheap, compact, and reliable — a single-purpose device that boots straight into the app and does nothing else.

---

## My Setup

| Component | Details | Link |
|---|---|---|
| **Computer** | Raspberry Pi Zero 2 W | [raspberrypi.com](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) |
| **Display** | 8" LCD 1024x768, 174x136mm *(recommended)* | [AliExpress](https://s.click.aliexpress.com/e/_c2z4vR9v) |
| **Display (alt)** | 7" LCD 1024x600, 165x100mm | [AliExpress](https://s.click.aliexpress.com/e/_c32YJ80L) |
| **Display controller** | Mini HDMI driver board, 5V via Micro USB | included with display |
| **Teleprompter frame** | Ulanzi RT02 with beam splitter glass | [AliExpress](https://s.click.aliexpress.com/e/_c3a2Kg9z) |
| **Input** | Bluetooth keyboard | |
| **OS** | Raspberry Pi OS Lite 64-bit | |

The 8" display (174mm wide) fits the Ulanzi RT02 holder (180mm) almost perfectly, covering the full beam splitter glass area with just 3mm clearance on each side. The 7" display also fits well with more clearance. The whole unit is powered independently — no phone battery anxiety, no notifications, no distractions. Scripts are managed wirelessly over WiFi via WinSCP.

---

## Features

- Auto-boots straight into the script selection menu (systemd service)
- **White text** for speech, **red text** for stage directions in `[ ]` brackets
- Adjustable scroll speed (1–10)
- Play/Pause, rewind, speed control
- Beam splitter glass correction (horizontal flip)
- Top fade effect — text fades out as it reaches the top
- Multilingual UI: Serbian, English, German, Spanish, French
- Language preference saved to `config.json`
- Shutdown option directly from the menu
- Exit to terminal option for maintenance

---

## Hardware Notes

**RPi Zero 2 W** — quad-core ARMv8, 512MB RAM, built-in WiFi + Bluetooth 4.2. The app uses pre-rendering (all text drawn to one large surface at startup) so scrolling is smooth even on this compact hardware.

**Display** — 8" LCD 1024x768, 174x136mm. Paired with a compact mini HDMI controller board from AliExpress. The controller is small enough to hide behind the display, keeping the setup clean. Powered via Micro USB 5V.

**Ulanzi RT02** — designed for phones and tablets but works perfectly as an open frame for a custom display. The 8" panel (174mm) fits the RT02 holder (180mm internal width) with 3mm clearance on each side, covering the full beam splitter glass area cleanly. Mounts on any standard tripod via 1/4" thread.

---

## Installation

### 1. Flash OS

Use Raspberry Pi Imager:
- **Device:** Raspberry Pi Zero 2 W
- **OS:** Raspberry Pi OS Lite (64-bit)
- **Edit Settings:**
  - Hostname: `teleprompter`
  - Username: `pi`
  - Password: your password
  - WiFi SSID + password
  - Enable SSH (password authentication)

### 2. First boot and SSH

Wait 2–3 minutes for first boot (Zero is slow), then:

```bash
ssh pi@teleprompter.local
sudo apt update && sudo apt upgrade -y
```

### 3. Install dependencies

```bash
sudo apt install python3-pygame python3-evdev fonts-dejavu-core bluetooth bluez -y
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### 4. Create folder structure

```bash
mkdir ~/teleprompter
mkdir ~/teleprompter/scripts
echo 'pi ALL=(ALL) NOPASSWD: /sbin/poweroff' | sudo tee /etc/sudoers.d/teleprompter
```

### 5. Upload files

Use WinSCP (SFTP, host: `teleprompter.local`) to upload:
- `teleprompter.py` → `/home/pi/teleprompter/`
- Your `.txt` script files → `/home/pi/teleprompter/scripts/`

> **Important:** Always use WinSCP for uploading Python files. Copy-pasting code through the terminal can corrupt formatting.

### 6. Auto-login

```bash
sudo raspi-config
# System Options → S6 Auto Login → Yes
```

### 7. Autostart on boot

```bash
echo 'if [ "$(tty)" = "/dev/tty1" ]; then /home/pi/teleprompter/start.sh; fi' >> ~/.profile
```

Create `start.sh`:

```bash
cat > ~/teleprompter/start.sh << 'EOF'
#!/bin/bash
export SDL_VIDEODRIVER=kmsdrm
export SDL_AUDIODRIVER=dummy
exec python3 /home/pi/teleprompter/teleprompter.py >> /home/pi/teleprompter/start.log 2>&1
EOF
chmod +x ~/teleprompter/start.sh
```

### 8. Reboot and test

```bash
sudo reboot
```

---

## Script Format

Scripts are plain `.txt` files in the `scripts/` folder. One file per episode.

```
Welcome to the show.

[Pause — look at the camera]

Today we are talking about artificial intelligence.

[Cut to B-roll]

The technology has evolved rapidly over the past decade.
```

- Normal lines → large white text (speech)
- Lines wrapped in `[ ]` → smaller red text (stage directions)
- Empty lines → paragraph spacer

---

## Keyboard Controls

| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `↑` | Speed up |
| `↓` | Slow down |
| `R` (hold) | Rewind (3× speed) |
| `ESC` | Back to menu |

---

## Display Resolution

Depending on which display you use, change these two lines at the top of `teleprompter.py`:

```python
# 8" display (recommended)
SCREEN_WIDTH  = 1024
SCREEN_HEIGHT = 768

# 7" display
SCREEN_WIDTH  = 1024
SCREEN_HEIGHT = 600
```

And update `/boot/config.txt` accordingly:

```ini
# 8" display
hdmi_cvt=1024 768 60 6 0 0 0

# 7" display
hdmi_cvt=1024 600 60 6 0 0 0
```

---

## Bluetooth Remote Controller *(coming soon)*

A dedicated wireless controller is currently in development — an ESP32-based Bluetooth HID device in a custom 3D-printed enclosure with:

- 5 onboard buttons (Play/Pause, Speed+, Speed−, ESC, Enter)
- 3 avionic plug outputs for external foot pedals
- Presents itself to the RPi as a standard Bluetooth keyboard — no drivers needed

This will be published as a separate project and linked here when ready.

---

If the display does not show correctly, add to `/boot/config.txt`:

```ini
# Force HDMI output
hdmi_force_hotplug=1

# Set resolution to match your display
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 768 60 6 0 0 0

# Disable overscan (black borders)
disable_overscan=1
```

Adjust `hdmi_cvt` values if you use a different display resolution.

---

## Beam Splitter Flip

The beam splitter glass mirrors the image. The flip direction is set in the script:

```python
# In apply_beam_splitter_flip() and load_and_run():
pygame.transform.flip(surface, True, False)   # horizontal flip (current)
pygame.transform.flip(surface, False, True)   # vertical flip
pygame.transform.flip(surface, True, True)    # both
```

Adjust to match your teleprompter frame orientation.

---

## Troubleshooting

**Black screen on boot:**
```bash
cat ~/teleprompter/start.log
```

**`fbcon not available` error:**
Use `kmsdrm` — do not use `fbcon` or `x11` on RPi Zero.

**Slow or stuttering scroll:**
Make sure the script uses pre-rendering (`big_surface`). Without it, the Zero CPU cannot render text fast enough.

**`fc-list` timeout warning:**
Normal on Zero — resolved by using `pygame.Font()` with a direct font path instead of `SysFont()`.

**Bluetooth not ready:**
```bash
sudo rfkill unblock bluetooth
sudo systemctl restart bluetooth
```

**Script does not autostart:**
Use `.profile`, not `.bashrc` or `.bash_profile`.
```bash
cat ~/.profile   # check the line is there at the bottom
```

---

## Project Structure

```
teleprompter/
├── teleprompter.py        # Main application
├── config.json            # Saved language preference
├── start.sh               # Startup script
├── start.log              # Runtime log (auto-generated)
└── scripts/
    ├── episode_01.txt
    ├── episode_02.txt
    └── ...
```

---

## License

MIT License. Use freely, modify freely, share freely.
