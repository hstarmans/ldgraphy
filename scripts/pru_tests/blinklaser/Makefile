AM335_BASE = ../../../am335x_pru_package
COMPILER=$(AM335_BASE)/pru_sw/utils/pasm 
FILENAME=blinklaser

.PHONY: clean all

all:
	$(COMPILER) -b $(FILENAME).p


clean: 
	rm -rf $(FILENAME).bin


