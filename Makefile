all: buildmo

buildmo:
	@echo "Building the mo files"
	./data/lang/update_translations.sh
