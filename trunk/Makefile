all:
	cd src/trayicon/ && make DESTDIR=$(DESTDIR)
	python ./setup.py install --root=$(DESTDIR)

clean:
	cd src/trayicon/ && make clean
