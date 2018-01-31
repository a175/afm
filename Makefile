INSTALLBIN = $(DESTDIR)/usr/bin
man1dir = $(mandir)/man1
INSTALLMAN1 = $(DESTDIR)$(man1dir)

all: bin/* man/*

bin/afm: source/afm.py
	cp source/afm.py bin/afm

install: all
	install -d  $(INSTALLBIN)
	install bin/* $(INSTALLBIN)

install-man: 
	install -d  $(INSTALLMAN1)
	install man/*.1 $(INSTALLMAN1)

clean: 
	echo "do nothing.."

