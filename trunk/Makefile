trayicon.so:
	cd src/trayicon/ && make DESTDIR=$(DESTDIR)

install: trayicon.so
	python ./setup.py install --root=$(DESTDIR)
	cp src/trayicon/build/lib*/trayicon.so $(DESTDIR)/usr/lib/python2.4/site-packages/libguzuta/

clean:
	cd src/trayicon/ && make clean

test:
	cd src/trayicon/ && make DESTDIR=$(DESTDIR)
