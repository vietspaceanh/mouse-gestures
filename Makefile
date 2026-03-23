PREFIX ?= $(HOME)/.local
BINDIR = $(PREFIX)/bin
SYSTEMD_DIR = $(HOME)/.config/systemd/user

SCRIPT = mouse-gestures.py
SERVICE = mouse-gestures.service

.PHONY: install uninstall enable disable

install: | $(BINDIR) $(SYSTEMD_DIR)
	install -m 755 $(SCRIPT) $(BINDIR)/$(SCRIPT)
	install -m 644 $(SERVICE) $(SYSTEMD_DIR)/$(SERVICE)
	systemctl --user daemon-reload

uninstall:
	-rm -f $(BINDIR)/$(SCRIPT)
	-rm -f $(SYSTEMD_DIR)/$(SERVICE)
	systemctl --user daemon-reload

enable: install
	systemctl --user enable --now $(SERVICE)

disable:
	systemctl --user disable --now $(SERVICE)

$(BINDIR):
	mkdir -p $(BINDIR)

$(SYSTEMD_DIR):
	mkdir -p $(SYSTEMD_DIR)