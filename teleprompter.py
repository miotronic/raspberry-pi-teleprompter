import pygame
import sys
import os
import subprocess
import json

# =============================================================================
# COMPATIBILITY
# This script is designed for Raspberry Pi Zero 2 W only.
# Pre-rendering and direct KMS/DRM driver are required due to the slower CPU.
#
# For Raspberry Pi 3, 4, and 5 use teleprompter_rpi4.py instead.
# =============================================================================

# =============================================================================
# DISPLAY SETTINGS
# Change SCREEN_WIDTH and SCREEN_HEIGHT to match your display resolution.
# Common sizes: 800x480 (7"), 1024x600 (7"), 1024x768 (8"), 1920x1080 (Full HD)
# Current: 8 inch 1024x768 LCD with mini HDMI controller board
# =============================================================================
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 480

# =============================================================================
# FONT SIZES
# FONT_SIZE       - main script text (the words you read on camera)
# STAGE_FONT_SIZE - director notes in [ ] brackets
# MENU_FONT_SIZE  - main menu and language selection
# =============================================================================
FONT_SIZE       = 60
STAGE_FONT_SIZE = 40
MENU_FONT_SIZE  = 48

# =============================================================================
# SCROLL SPEED
# Starting scroll speed (1 = slowest). User can change with UP/DOWN arrows.
# Range is 1-10. Increase default if your scripts are short.
# =============================================================================
SCROLL_SPEED = 1

# =============================================================================
# COLORS (R, G, B)
# =============================================================================
BG_COLOR        = (0,   0,   0)   # Background -- pure black
TEXT_COLOR      = (255, 255, 255) # Main script text -- white
STAGE_COLOR     = (220,  50,  50) # Director notes [ ] -- red
HIGHLIGHT_COLOR = (0,   150, 255) # Selected menu item -- blue
SHUTDOWN_COLOR  = (200,  50,  50) # Shutdown option -- red
SETTINGS_COLOR  = (150, 150,   0) # Settings option -- yellow

# =============================================================================
# FILE PATHS
# Scripts folder must contain .txt files -- one file per episode.
# Config file stores the selected language between reboots.
# =============================================================================
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

# =============================================================================
# FONT PATH
# Using direct path instead of SysFont -- SysFont causes timeout on RPi Zero
# due to fc-list being slow on low-powered hardware.
# =============================================================================
FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

# =============================================================================
# UI TRANSLATIONS
# Add or edit languages here. Each language needs these keys:
#   name, choose, settings, shutdown, choose_lang, back
# =============================================================================
LANGUAGES = {
    'sr': {
        'name':        'Srpski',
        'choose':      'Odaberi skriptu:',
        'settings':    'Podesavanja',
        'shutdown':    'Ugasi RPi',
        'exit_shell':  'Izadji u terminal',
        'choose_lang': 'Izaberi jezik:',
        'back':        'Nazad',
    },
    'en': {
        'name':        'English',
        'choose':      'Choose script:',
        'settings':    'Settings',
        'shutdown':    'Shutdown RPi',
        'exit_shell':  'Exit to terminal',
        'choose_lang': 'Choose language:',
        'back':        'Back',
    },
    'de': {
        'name':        'Deutsch',
        'choose':      'Skript wahlen:',
        'settings':    'Einstellungen',
        'shutdown':    'RPi ausschalten',
        'exit_shell':  'Zum Terminal',
        'choose_lang': 'Sprache wahlen:',
        'back':        'Zuruck',
    },
    'es': {
        'name':        'Espanol',
        'choose':      'Elegir guion:',
        'settings':    'Configuracion',
        'shutdown':    'Apagar RPi',
        'exit_shell':  'Salir al terminal',
        'choose_lang': 'Elegir idioma:',
        'back':        'Volver',
    },
    'fr': {
        'name':        'Francais',
        'choose':      'Choisir script:',
        'settings':    'Parametres',
        'shutdown':    'Eteindre RPi',
        'exit_shell':  'Quitter vers terminal',
        'choose_lang': 'Choisir langue:',
        'back':        'Retour',
    },
}

# Order in which languages appear in the language selection screen
LANG_ORDER = ['sr', 'en', 'de', 'es', 'fr']


# =============================================================================
# CONFIG -- load and save selected language to disk
# =============================================================================

def load_config():
    """Load saved language code from config.json. Returns None if not found."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            return data.get('language', None)
    return None

def save_config(lang):
    """Save selected language code to config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'language': lang}, f)


# =============================================================================
# SCRIPTS -- get list of available .txt scripts from the scripts folder
# =============================================================================

def get_scripts():
    """Return sorted list of .txt filenames from the scripts directory."""
    files = sorted([f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.txt')])
    return files


# =============================================================================
# BEAM SPLITTER FLIP
# The beam splitter glass reflects the image, so we need to flip it.
# This function is called at the end of every draw function.
#
# pygame.transform.flip(surface, horizontal, vertical)
#
#   Text upside down but not mirrored  -> flip(False, True)   <-- current
#   Text mirrored but not upside down  -> flip(True,  False)
#   Text both upside down and mirrored -> flip(True,  True)
#   No flip needed                     -> remove the flip call
# =============================================================================

def apply_beam_splitter_flip(screen):
    """Flip the entire screen for beam splitter glass correction."""
    flipped = pygame.transform.flip(screen, True, False)
    screen.blit(flipped, (0, 0))


# =============================================================================
# LANGUAGE SELECTION SCREEN
# =============================================================================

def show_language_select(screen, font, selected, current_lang=None):
    """Draw the language selection screen."""
    screen.fill(BG_COLOR)
    lang = LANGUAGES.get(current_lang, LANGUAGES['en'])

    # Title
    title = font.render(lang['choose_lang'], True, (150, 150, 150))
    screen.blit(title, (20, 20))

    item_height     = 55
    visible_start_y = 90

    # Language options
    for i, code in enumerate(LANG_ORDER):
        color = HIGHLIGHT_COLOR if i == selected else TEXT_COLOR
        text = font.render(LANGUAGES[code]['name'], True, color)
        screen.blit(text, (40, visible_start_y + i * item_height))

    # Back button
    back_color = SETTINGS_COLOR if selected == len(LANG_ORDER) else (100, 100, 100)
    back = font.render(lang['back'], True, back_color)
    screen.blit(back, (40, visible_start_y + len(LANG_ORDER) * item_height))

    apply_beam_splitter_flip(screen)
    pygame.display.flip()


def language_select_screen(screen, font, current_lang):
    """Handle input on the language selection screen. Returns selected language code."""
    selected = LANG_ORDER.index(current_lang) if current_lang in LANG_ORDER else 0
    show_language_select(screen, font, selected, current_lang)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                total = len(LANG_ORDER) + 1  # languages + back button
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % total
                    show_language_select(screen, font, selected, current_lang)
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % total
                    show_language_select(screen, font, selected, current_lang)
                if event.key == pygame.K_RETURN:
                    if selected == len(LANG_ORDER):
                        return current_lang  # Back -- no change
                    new_lang = LANG_ORDER[selected]
                    save_config(new_lang)
                    return new_lang
                if event.key == pygame.K_ESCAPE:
                    return current_lang  # ESC -- no change


# =============================================================================
# MAIN MENU
# =============================================================================

def show_menu(screen, font, scripts, selected, lang_code):
    """Draw the main script selection menu."""
    lang = LANGUAGES[lang_code]
    screen.fill(BG_COLOR)

    # Title
    title = font.render(lang['choose'], True, (150, 150, 150))
    screen.blit(title, (20, 20))

    item_height     = 55
    visible_start_y = 90
    max_visible     = (SCREEN_HEIGHT - visible_start_y) // item_height - 2
    total           = len(scripts) + 3  # scripts + Settings + Shutdown + Exit

    # Scroll the list so the selected item stays visible
    if selected < max_visible // 2:
        scroll_offset = 0
    elif selected > total - max_visible // 2:
        scroll_offset = max(0, total - max_visible)
    else:
        scroll_offset = selected - max_visible // 2

    # Script list items
    for i in range(scroll_offset, min(scroll_offset + max_visible, len(scripts))):
        color = HIGHLIGHT_COLOR if i == selected else TEXT_COLOR
        text = font.render(scripts[i].replace('.txt', ''), True, color)
        screen.blit(text, (40, visible_start_y + (i - scroll_offset) * item_height))

    settings_idx = len(scripts)
    shutdown_idx  = len(scripts) + 1
    exit_idx      = len(scripts) + 2

    # Settings option
    if scroll_offset + max_visible > len(scripts):
        settings_color = SETTINGS_COLOR if selected == settings_idx else (100, 100, 100)
        settings_text  = font.render('* ' + lang['settings'], True, settings_color)
        y_pos = visible_start_y + (settings_idx - scroll_offset) * item_height
        if y_pos < SCREEN_HEIGHT:
            screen.blit(settings_text, (40, y_pos))

    # Shutdown option
    if scroll_offset + max_visible > len(scripts) + 1:
        shutdown_color = SHUTDOWN_COLOR if selected == shutdown_idx else (100, 100, 100)
        shutdown_text  = font.render('[ ' + lang['shutdown'] + ' ]', True, shutdown_color)
        y_pos = visible_start_y + (shutdown_idx - scroll_offset) * item_height
        if y_pos < SCREEN_HEIGHT:
            screen.blit(shutdown_text, (40, y_pos))

    # Exit to terminal option
    if scroll_offset + max_visible > len(scripts) + 2:
        exit_color = SETTINGS_COLOR if selected == exit_idx else (100, 100, 100)
        exit_text  = font.render('> ' + lang['exit_shell'], True, exit_color)
        y_pos = visible_start_y + (exit_idx - scroll_offset) * item_height
        if y_pos < SCREEN_HEIGHT:
            screen.blit(exit_text, (40, y_pos))

    apply_beam_splitter_flip(screen)
    pygame.display.flip()


# =============================================================================
# TEXT PARSER
# Splits script text into rendered pygame surfaces.
# Lines wrapped in [ ] are treated as director notes (stage directions).
# All lines are word-wrapped to fit SCREEN_WIDTH.
# =============================================================================

def parse_lines(text, font_normal, font_stage):
    """
    Parse script text and return list of (surface, height) tuples.
    Empty lines return (None, FONT_SIZE) as spacers.
    Lines in [ ] are rendered in STAGE_COLOR with smaller font.
    All other lines are rendered in TEXT_COLOR with main font.
    """
    rendered = []
    lines = text.split('\n')

    for line in lines:
        stripped = line.strip()

        if stripped == '':
            # Empty line -- used as spacer between paragraphs
            rendered.append((None, FONT_SIZE))

        elif stripped.startswith('[') and stripped.endswith(']'):
            # Director note -- smaller red text
            words = stripped.split()
            current_line = ''
            for word in words:
                test = current_line + ' ' + word if current_line else word
                if font_stage.size(test)[0] <= SCREEN_WIDTH - 40:
                    current_line = test
                else:
                    rendered.append((font_stage.render(current_line, True, STAGE_COLOR), STAGE_FONT_SIZE))
                    current_line = word
            if current_line:
                rendered.append((font_stage.render(current_line, True, STAGE_COLOR), STAGE_FONT_SIZE))

        else:
            # Normal script text -- large white text
            words = stripped.split()
            current_line = ''
            for word in words:
                test = current_line + ' ' + word if current_line else word
                if font_normal.size(test)[0] <= SCREEN_WIDTH - 40:
                    current_line = test
                else:
                    rendered.append((font_normal.render(current_line, True, TEXT_COLOR), FONT_SIZE))
                    current_line = word
            if current_line:
                rendered.append((font_normal.render(current_line, True, TEXT_COLOR), FONT_SIZE))

    return rendered


# =============================================================================
# SCRIPT PLAYER
# Pre-renders all lines onto one large surface at startup.
# This is critical for RPi Zero performance -- without pre-rendering,
# the Zero's ARMv6 CPU cannot render text fast enough for smooth scrolling.
# =============================================================================

def load_and_run(screen, filename):
    """Load a script file and run the teleprompter scroll loop."""
    font_normal = pygame.font.Font(FONT_PATH, FONT_SIZE)
    font_stage  = pygame.font.Font(FONT_PATH, STAGE_FONT_SIZE)

    # Load and parse the script text
    with open(os.path.join(SCRIPTS_DIR, filename), 'r', encoding='utf-8') as f:
        text = f.read()
    rendered_lines = parse_lines(text, font_normal, font_stage)

    # Calculate total height of all content
    total_height = sum((FONT_SIZE if s is None else size + 10) for s, size in rendered_lines)
    total_height += SCREEN_HEIGHT * 2  # padding at top and bottom

    # Pre-render all lines onto one big surface.
    # The CPU renders text only once at startup -- scrolling just moves the surface.
    # Pre-render all lines onto one big surface.
    # Text starts from SCREEN_HEIGHT so the screen is empty at the beginning.
    big_surface = pygame.Surface((SCREEN_WIDTH, total_height))
    big_surface.fill(BG_COLOR)
    y = SCREEN_HEIGHT  # start with one full screen of top padding
    for surface, size in rendered_lines:
        if surface is None:
            y += FONT_SIZE  # empty line spacer
        else:
            x = (SCREEN_WIDTH - surface.get_width()) // 2  # center horizontally
            big_surface.blit(surface, (x, y))
            y += size + 10  # line spacing

    # scroll_y starts at SCREEN_HEIGHT // 2 so first line appears at screen center.
    # Change to 0 to start text from very top, or SCREEN_HEIGHT to start from bottom.
    # scroll_y   = SCREEN_HEIGHT // 2
    scroll_y = int(SCREEN_HEIGHT * 0.3)
    max_scroll = total_height - SCREEN_HEIGHT
    speed      = SCROLL_SPEED
    paused     = False
    rewinding  = False
    clock      = pygame.time.Clock()

    while True:
        # Handle keyboard input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True                        # Back to menu
                if event.key == pygame.K_SPACE:
                    paused = not paused                # Toggle pause
                if event.key == pygame.K_UP:
                    speed = min(speed + 1, 10)         # Speed up
                if event.key == pygame.K_DOWN:
                    speed = max(speed - 1, 1)          # Slow down
                if event.key == pygame.K_r:
                    rewinding = True
                    paused = False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_r:
                    rewinding = False

        # Update scroll position
        if rewinding:
            scroll_y = max(0, scroll_y - speed * 3)        # Rewind at 3x speed
        elif not paused:
            scroll_y = min(scroll_y + speed, max_scroll)   # Scroll forward

        # Crop full screen frame
        # frame = big_surface.subsurface((0, scroll_y, SCREEN_WIDTH, SCREEN_HEIGHT)).copy()
        frame = big_surface.subsurface((0, scroll_y, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.7))).copy()
        # Apply fade only at the top -- text fades out as it reaches the top of the screen.
        # FADE_ZONE controls how many pixels fade (top 40% of screen height).
        # Increase for more gradual fade, decrease for sharper transition.
        FADE_ZONE = int(SCREEN_HEIGHT * 0.4)
        fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        fade_surface.fill((0, 0, 0, 0))
        for y_px in range(FADE_ZONE):
            # Top fade only -- fully black at top, transparent at FADE_ZONE
            alpha = int(255 * (1.0 - y_px / FADE_ZONE))
            pygame.draw.line(fade_surface, (0, 0, 0, alpha), (0, y_px), (SCREEN_WIDTH, y_px))

        padded = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        padded.fill(BG_COLOR)
        padded.blit(frame, (0, 0))
        padded.blit(fade_surface, (0, 0))

        # Flip for beam splitter glass correction.
        # pygame.transform.flip(surface, flip_horizontal, flip_vertical)
        #
        #   Text upside down, not left-right -> flip(False, True)
        #   Text left-right, not upside down -> flip(True,  False)  <-- current setting
        #   Text both upside down and left-right -> flip(True, True)
        #   No correction needed             -> remove flip, use: screen.blit(frame, (0, 0))
        flipped = pygame.transform.flip(padded, True, False)
        screen.blit(flipped, (0, 0))

        pygame.display.flip()
        clock.tick(30)  # 30 FPS


# =============================================================================
# MAIN -- entry point
# Sets up SDL for RPi Zero (kmsdrm, no X server), initializes pygame,
# loads config, and runs the main menu loop.
# =============================================================================

def main():
    # Use KMS/DRM driver -- required on RPi Zero (no X server available)
    # Do NOT use SDL_VIDEODRIVER=x11 or SDL_VIDEODRIVER=fbcon on RPi Zero
    os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'  # Suppress ALSA audio errors

    pygame.init()
    pygame.display.init()
    pygame.mouse.set_visible(False)  # Hide mouse cursor

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Teleprompter")

    # Load menu font -- using direct path, not SysFont (SysFont is too slow on Zero)
    font = pygame.font.Font(FONT_PATH, MENU_FONT_SIZE)

    # Load saved language or show language selection on first boot
    lang_code = load_config()
    if lang_code is None or lang_code not in LANGUAGES:
        lang_code = language_select_screen(screen, font, 'en')
        save_config(lang_code)

    selected = 0

    # Main menu loop
    while True:
        scripts = get_scripts()
        total   = len(scripts) + 3  # scripts + Settings + Shutdown + Exit

        show_menu(screen, font, scripts, selected, lang_code)

        # Wait for user to press Enter
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % total
                        show_menu(screen, font, scripts, selected, lang_code)
                    if event.key == pygame.K_DOWN:
                        selected = (selected + 1) % total
                        show_menu(screen, font, scripts, selected, lang_code)
                    if event.key == pygame.K_RETURN:
                        waiting = False

        if selected == len(scripts):
            # Settings -- open language selection
            lang_code = language_select_screen(screen, font, lang_code)
            selected = 0

        elif selected == len(scripts) + 1:
            # Shutdown RPi
            pygame.quit()
            subprocess.call(['sudo', 'poweroff'])
            sys.exit()

        elif selected == len(scripts) + 2:
            # Exit to terminal -- quit pygame and drop to shell
            pygame.quit()
            sys.exit()

        else:
            # Load and run selected script
            result = load_and_run(screen, scripts[selected])
            if not result:
                break  # Quit if load_and_run returned False

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
