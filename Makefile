PREFIX ?= /usr/local
DESTDIR ?=
PYTHON ?= python3
ZSH_COMPLETION_DIR ?= $(PREFIX)/share/zsh/site-functions

.PHONY: test check install uninstall deb

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests -v

check:
	$(PYTHON) -c 'from pathlib import Path; p = Path("bin/diskintegrity"); compile(p.read_text(), str(p), "exec")'

install:
	install -d "$(DESTDIR)$(PREFIX)/bin" "$(DESTDIR)$(ZSH_COMPLETION_DIR)"
	install -m 755 bin/diskintegrity "$(DESTDIR)$(PREFIX)/bin/diskintegrity"
	install -m 644 completions/_diskintegrity "$(DESTDIR)$(ZSH_COMPLETION_DIR)/_diskintegrity"

uninstall:
	rm -f "$(DESTDIR)$(PREFIX)/bin/diskintegrity" "$(DESTDIR)$(ZSH_COMPLETION_DIR)/_diskintegrity"

deb:
	./scripts/build-deb.sh
