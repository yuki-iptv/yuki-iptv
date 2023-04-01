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
	pylint usr/lib/yuki-iptv/thirdparty/conversion.py
	pylint usr/lib/yuki-iptv/thirdparty/series.py
	pylint usr/lib/yuki-iptv/yuki_iptv/
	pylint usr/lib/yuki-iptv/yuki-iptv.py
	pylint tests/

test:
	python3 -m pytest tests
