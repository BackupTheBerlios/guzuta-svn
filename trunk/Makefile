trayicon.so:
	cd src/trayicon/ && make DESTDIR=$(DESTDIR)

install: trayicon.so
	mkdir $(DESTDIR)/lib/guzuta/
	cp src/trayicon/build/lib*/trayicon.so $(DESTDIR)/lib/guzuta/
	python ./setup.py install --root=$(DESTDIR)

clean:
	cd src/trayicon/ && make clean

test:
	cd src/trayicon/ && make DESTDIR=$(DESTDIR)
