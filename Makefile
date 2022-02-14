all: buildmo

buildmo:
	# WARNING: the second sed below will only works correctly with the languages that don't contain "-"
	for file in `ls po/*.po`; do \
		lang=`echo $$file | sed 's@po/@@' | sed 's/\.po//' | sed 's/astronciaiptv-//'`; \
		install -d usr/share/locale/$$lang/LC_MESSAGES/; \
		msgfmt -o usr/share/locale/$$lang/LC_MESSAGES/astronciaiptv.mo $$file; \
	done \

clean:
	rm -rf usr/share/locale

lint:
	pylint usr/lib/astronciaiptv/thirdparty/conversion.py
	pylint usr/lib/astronciaiptv/thirdparty/series.py
	pylint usr/lib/astronciaiptv/astroncia/
	pylint usr/lib/astronciaiptv/astroncia_iptv.py
