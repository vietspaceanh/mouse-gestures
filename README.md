# Mouse Gestures

This daemon maps simple mouse gestures to custom keybindings. While originally designed to port Vivaldi-style gestures to Firefox, its global keybinding approach makes it environment-agnostic. It functions across the entire OS, e.g. it can also close/re-open tabs in a file manager.

**Usage**:
Hold the right mouse button and draw a pattern to trigger an action:

| Gesture | Action |
|---------|--------|
| L shape (down → right) | Close tab (Ctrl+W) |
| Top right (up → right) | Reopen closed tab (Ctrl+Shift+T) |
| Right | New tab (Ctrl+T) |
| Left | Previous tab (Ctrl+Tab) |
| Up | Go to top (Ctrl+Home) |
| Down | Go to end (Ctrl+End) |
| Up then down | Refresh (F5) |

Add custom gestures by editing the `GESTURES` dict in `mouse-gestures.py`.

Works on both X11 and Wayland via `python-evdev`.

## Configuration

Edit the top of `mouse-gestures.py`:

```python
DEVICE            = "/dev/input/by-id/your-mouse-device"
SENSITIVITY       = 1.1     # Cursor speed multiplier
SEGMENT_THRESHOLD = 20      # Pixels before a direction registers
```

Find your device path:
```
ls /dev/input/by-id/
```

## Dependencies

- Arch Linux: `sudo pacman -S python-evdev`

## Install

```
make enable
```

## Uninstall

```
make disable
make uninstall
```