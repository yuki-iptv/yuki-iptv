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
	flake8 .

test:
	mkdir -p "/tmp/yuki-iptv-py"
	PYTHONPYCACHEPREFIX="/tmp/yuki-iptv-py" python3 -m pytest tests
	rm -rf "/tmp/yuki-iptv-py"
