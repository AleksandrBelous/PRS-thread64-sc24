all:
	$(MAKE) -C "/home/nemo/PRS-thread64-sc24/solvers/kissat-inc/build"
kissat:
	$(MAKE) -C "/home/nemo/PRS-thread64-sc24/solvers/kissat-inc/build" kissat
tissat:
	$(MAKE) -C "/home/nemo/PRS-thread64-sc24/solvers/kissat-inc/build" tissat
clean:
	rm -f "/home/nemo/PRS-thread64-sc24/solvers/kissat-inc"/makefile
	-$(MAKE) -C "/home/nemo/PRS-thread64-sc24/solvers/kissat-inc/build" clean
	rm -rf "/home/nemo/PRS-thread64-sc24/solvers/kissat-inc/build"
coverage:
	$(MAKE) -C "/home/nemo/PRS-thread64-sc24/solvers/kissat-inc/build" coverage
indent:
	$(MAKE) -C "/home/nemo/PRS-thread64-sc24/solvers/kissat-inc/build" indent
test:
	$(MAKE) -C "/home/nemo/PRS-thread64-sc24/solvers/kissat-inc/build" test
.PHONY: all clean coverage indent kissat test tissat
