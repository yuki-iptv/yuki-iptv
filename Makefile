all: buildmo

buildmo:
	# WARNING: the second sed below will only works correctly with the languages that don't contain "-"
	for file in `ls po/*.po`; do \
		lang=`echo $$file | sed 's@po/@@' | sed 's/\.po//' | sed 's/yuki-iptv-//'`; \
		install -d usr/share/locale/$$lang/LC_MESSAGES/; \
		msgfmt -o usr/share/locale/$$lang/LC_MESSAGES/yuki-iptv.mo $$file; \
	done \

clean:
	rm -rf usr/share/locale

lint:
	black --check --diff usr/lib/yuki-iptv/yuki_iptv usr/lib/yuki-iptv/yuki-iptv.py tests generate_desktop_files
	flake8 .

black:
	black usr/lib/yuki-iptv/yuki_iptv usr/lib/yuki-iptv/yuki-iptv.py tests generate_desktop_files

test:
	mkdir -p "/tmp/yuki-iptv-py"
	PYTHONPYCACHEPREFIX="/tmp/yuki-iptv-py" python3 -m pytest tests
	rm -rf "/tmp/yuki-iptv-py"
