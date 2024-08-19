DESTDIR :=
PREFIX := /usr

clean-unused-shm-objects: clean-unused-shm-objects.c
	$(CC) -o $@ $<

install:
	mkdir -p "${DESTDIR}${PREFIX}/bin"
	install clean-unused-shm-objects "${DESTDIR}${PREFIX}/bin"

clean:
	rm clean-unused-shm-objects

.PHONY: install clean
