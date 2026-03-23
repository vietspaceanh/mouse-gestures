# Mouse Gestures

A mouse gesture daemon that maps simple gestures to keybindings, similar to Vivaldi browser. Hold right mouse button and draw to trigger actions:

| Gesture | Action |
|---------|--------|
| L shape (down → right) | Close tab (Ctrl+W) |
| Right | New tab (Ctrl+T) |
| Left | Previous tab (Ctrl+Tab) |
| Up | Go to top (Ctrl+Home) |
| Down | Go to end (Ctrl+End) |

Add custom gestures by editing the `GESTURES` dict in `mouse-gestures.py`.

Works on both X11 and Wayland via `python-evdev`.

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