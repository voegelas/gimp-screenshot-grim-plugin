PLUGIN := screenshot-grim

GIMP_VERSION := 3.0

PLUGIN_PROGRAM := $(PLUGIN).py

PACKAGE := gimp-$(PLUGIN)-plugin

prefix := /usr
exec_prefix := $(prefix)
datarootdir := $(prefix)/share
libdir := $(exec_prefix)/lib64

GIMP3_LOCALEDIR ?= $(datarootdir)/locale
localedir := $(GIMP3_LOCALEDIR)

GIMP3_PLUGINDIR ?= $(libdir)/gimp/$(GIMP_VERSION)
plugindir ?= $(GIMP3_PLUGINDIR)/plug-ins/$(PLUGIN)

XDG_CONFIG_HOME ?= ${HOME}/.config
GIMP3_DIRECTORY ?= $(XDG_CONFIG_HOME)/GIMP/$(GIMP_VERSION)
user_plugindir := $(GIMP3_DIRECTORY)/plug-ins/$(PLUGIN)
user_localedir := $(user_plugindir)/locale

MSGFMT := msgfmt
LOCALES := $(patsubst %.po,%,$(subst po/,,$(wildcard po/*.po)))
CATALOGS = $(patsubst locale/%,%,$(wildcard locale/*/*/*.mo))

INSTALL := install
INSTALL_PROGRAM := $(INSTALL)
INSTALL_DATA := $(INSTALL) -m 644

all:

install:
	$(INSTALL_PROGRAM) -D $(PLUGIN_PROGRAM) $(DESTDIR)$(plugindir)/$(PLUGIN_PROGRAM)
	for f in $(CATALOGS); do \
		$(INSTALL_DATA) -D locale/$$f $(DESTDIR)$(localedir)/$$f; \
	done

install-user:
	$(INSTALL_PROGRAM) -D $(PLUGIN_PROGRAM) $(DESTDIR)$(user_plugindir)/$(PLUGIN_PROGRAM)
	for f in $(CATALOGS); do \
		$(INSTALL_DATA) -D locale/$$f $(DESTDIR)$(user_localedir)/$$f; \
	done

locales:
	for l in $(LOCALES); do \
		dir=locale/$$l/LC_MESSAGES; \
		po=po/$$l.po; \
		mo=$$dir/$(PACKAGE).mo; \
		$(INSTALL) -d $$dir; \
		if [ ! -f "$$mo" -o "$$mo" -ot "$$po" ]; then \
			$(MSGFMT) -o $$mo $$po; \
		fi; \
	done

.PHONY: all install install-user locales
