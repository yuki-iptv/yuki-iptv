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
