all: buildmo

buildmo:
	# WARNING: the second sed below will only works correctly with the languages that don't contain "-"
	for file in `ls po/*.po`; do \
		lang=`echo $$file | sed 's@po/@@' | sed 's/\.po//' | sed 's/astronciaiptv-//'`; \
		install -d data/lang/$$lang/LC_MESSAGES/; \
		msgfmt -o data/lang/$$lang/LC_MESSAGES/astronciaiptv.mo $$file; \
	done \

clean:
	rm -rf data/lang
