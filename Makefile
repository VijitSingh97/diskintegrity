PREFIX ?= /usr/local
ZSH_COMPLETION_DIR ?= $(PREFIX)/share/zsh/site-functions

.PHONY: test check install uninstall

test:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v

check:
	python3 -c 'from pathlib import Path; p = Path("bin/diskintegrity"); compile(p.read_text(), str(p), "exec")'

install:
	install -d "$(DESTDIR)$(PREFIX)/bin" "$(DESTDIR)$(ZSH_COMPLETION_DIR)"
	install -m 755 bin/diskintegrity "$(DESTDIR)$(PREFIX)/bin/diskintegrity"
	install -m 644 completions/_diskintegrity "$(DESTDIR)$(ZSH_COMPLETION_DIR)/_diskintegrity"

uninstall:
	rm -f "$(DESTDIR)$(PREFIX)/bin/diskintegrity" "$(DESTDIR)$(ZSH_COMPLETION_DIR)/_diskintegrity"
