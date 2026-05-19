#!/usr/bin/env python3
"""Mouse gesture daemon — grab a device, draw gestures with RMB held."""

import time
import sys
import threading
from evdev import InputDevice, UInput, ecodes as e, list_devices

# ==========================================
# CONFIGURATION
# ==========================================

DEVICE            = "/dev/input/by-id/usb-Compx_2.4G_Receiver-if01-event-mouse"
SENSITIVITY       = 1.1     # Cursor speed multiplier
SEGMENT_THRESHOLD = 20    # Pixels before a direction segment registers

# --- Gesture map ---
GESTURES: dict[tuple, list | callable] = {
    ("DOWN", "RIGHT"): [e.KEY_LEFTCTRL, e.KEY_W],
    ("UP",  "RIGHT"):  [e.KEY_LEFTCTRL, e.KEY_LEFTSHIFT, e.KEY_T],
    ("LEFT",):         [e.KEY_LEFTCTRL, e.KEY_TAB],
    ("RIGHT",):        [e.KEY_LEFTCTRL, e.KEY_T],
    ("UP",   "DOWN"):  [e.KEY_F5],
    ("UP",):           [e.KEY_LEFTCTRL, e.KEY_HOME],
    ("DOWN",):         [e.KEY_LEFTCTRL, e.KEY_END],
}

# ==========================================
# FIND KEYBOARD DEVICE (for Super key monitoring)
# ==========================================

def find_keyboard_device() -> InputDevice | None:
    """
    Find a keyboard device that has the Super key.
    We do NOT grab it — only peek at key state.
    """
    for path in list_devices():
        try:
            dev = InputDevice(path)
            caps = dev.capabilities()
            keys = caps.get(e.EV_KEY, [])
            if e.KEY_LEFTMETA in keys or e.KEY_RIGHTMETA in keys:
                print(f"Super key monitor: {dev.path}  ({dev.name})")
                return dev
        except Exception:
            continue
    return None

# ==========================================
# SUPER KEY STATE TRACKER
# ==========================================

super_held = False   # global flag, written by kb thread, read by mouse loop

def monitor_super_key(kb_dev: InputDevice) -> None:
    """Background thread: watch for Super press/release, forward to UInput."""
    global super_held
    try:
        for ev in kb_dev.read_loop():
            if ev.type == e.EV_KEY and ev.code in (e.KEY_LEFTMETA, e.KEY_RIGHTMETA):
                if ev.value == 1:
                    super_held = True
                    ui.write(e.EV_KEY, ev.code, 1); ui.syn()
                elif ev.value == 0:
                    super_held = False
                    ui.write(e.EV_KEY, ev.code, 0); ui.syn()
    except Exception as ex:
        print(f"[kb monitor] stopped: {ex}")

# ==========================================
# SETUP
# ==========================================

try:
    mouse = InputDevice(DEVICE)
    mouse.grab()
except Exception as ex:
    sys.exit(f"Error opening device: {ex}")

kb = find_keyboard_device()
if kb is None:
    print("WARNING: No keyboard with Super key found — Super pass-through disabled.")
else:
    t = threading.Thread(target=monitor_super_key, args=(kb,), daemon=True)
    t.start()

_extra_keys = {k for keys in GESTURES.values()
                 if isinstance(keys, list) for k in keys}

caps = {
    e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL, e.REL_HWHEEL,
               *[getattr(e, a) for a in ["REL_WHEEL_HI_RES", "REL_HWHEEL_HI_RES"]
                 if hasattr(e, a)]],
    e.EV_KEY: list({e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE,
                    e.BTN_SIDE, e.BTN_EXTRA} | _extra_keys),
}

ui = UInput(events=caps, name="Gesture Mouse", vendor=0x1111, product=0x2222)

# ==========================================
# HELPERS
# ==========================================

_KEY_NAME = lambda k: e.keys.get(k, str(k))

def press_keys(keys: list) -> None:
    for k in keys:            ui.write(e.EV_KEY, k, 1)
    ui.syn()
    time.sleep(0.02)
    for k in reversed(keys):  ui.write(e.EV_KEY, k, 0)
    ui.syn()

def right_click() -> None:
    ui.write(e.EV_KEY, e.BTN_RIGHT, 1); ui.syn()
    time.sleep(0.01)
    ui.write(e.EV_KEY, e.BTN_RIGHT, 0); ui.syn()

def run_gesture(sequence: list) -> None:
    action = GESTURES.get(tuple(sequence))
    if action is None:
        print(f"Unknown gesture: {sequence}")
    elif callable(action):
        action()
    else:
        print(f"Gesture {tuple(sequence)} → "
              f"{'+'.join(_KEY_NAME(k) for k in action)}")
        press_keys(action)

def apply_sensitivity(value: float, remainder: float) -> tuple[int, float]:
    raw  = value * SENSITIVITY + remainder
    move = int(raw)
    return move, raw - move


# ==========================================
# MAIN LOOP
# ==========================================

print(f"Listening on : {DEVICE}  (sensitivity {SENSITIVITY}x)")
print("Active gestures:")
for seq, action in GESTURES.items():
    label = ("+".join(_KEY_NAME(k) for k in action)
             if isinstance(action, list) else action.__name__)
    print(f"  {seq!s:<30} → {label}")

tracking      = False
sequence      = []
dx = dy       = 0
rem_x = rem_y = 0.0

try:
    for ev in mouse.read_loop():

        # ----------------------------------------
        # SUPER HELD — forward via UInput (same device as Super key)
        # ----------------------------------------
        if super_held:
            if tracking:
                tracking = False
                sequence = []
                dx = dy = 0
                ui.write(e.EV_KEY, e.BTN_RIGHT, 0); ui.syn()
            if ev.type in caps and ev.code in caps[ev.type]:
                ui.write(ev.type, ev.code, ev.value)
            if ev.type == e.EV_SYN:
                ui.syn()
            continue

        # ----------------------------------------
        # NORMAL (no Super) — gesture logic
        # ----------------------------------------

        # --- Sync ---
        if ev.type == e.EV_SYN:
            ui.syn()

        # --- Right button: start / stop gesture ---
        elif ev.type == e.EV_KEY and ev.code == e.BTN_RIGHT:
            if ev.value == 1:                          # press
                tracking, sequence, dx, dy = True, [], 0, 0
                rem_x = rem_y = 0.0

            elif ev.value == 0:                        # release
                tracking = False
                right_click() if not sequence else run_gesture(sequence)

        # --- Movement ---
        elif ev.type == e.EV_REL:

            if tracking and ev.code in (e.REL_X, e.REL_Y):
                if ev.code == e.REL_X: dx += ev.value
                else:                  dy += ev.value

                if max(abs(dx), abs(dy)) > SEGMENT_THRESHOLD:
                    direction = ("LEFT"  if dx < 0 else "RIGHT") if abs(dx) > abs(dy) \
                           else ("UP"    if dy < 0 else "DOWN")

                    if not sequence or sequence[-1] != direction:
                        sequence.append(direction)

                    dx = dy = 0

            if ev.code == e.REL_X:
                move, rem_x = apply_sensitivity(ev.value, rem_x)
                if move: ui.write(e.EV_REL, e.REL_X, move)

            elif ev.code == e.REL_Y:
                move, rem_y = apply_sensitivity(ev.value, rem_y)
                if move: ui.write(e.EV_REL, e.REL_Y, move)

            elif ev.code in caps[e.EV_REL]:
                ui.write(ev.type, ev.code, ev.value)

        # --- Everything else ---
        elif ev.type in caps and ev.code in caps[ev.type]:
            ui.write(ev.type, ev.code, ev.value)

except KeyboardInterrupt:
    print("\nExiting…")
finally:
    try: mouse.ungrab()
    except: pass
    ui.close()
