COMPILER=pasm 
FILENAME=blinklaser1

.PHONY: clean all

all:
	$(COMPILER) -b $(FILENAME).p
	$(COMPILER) -b on.p
	$(COMPILER) -b off.p

clean: 
	rm -rf $(FILENAME).bin


