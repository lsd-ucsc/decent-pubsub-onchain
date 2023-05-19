MODULES        := \
	PubSub \
	tests
SOLC_VERSION   := v0.8.20
MKFILE_PATH    := $(abspath $(lastword $(MAKEFILE_LIST)))
CURRENT_DIR    := $(dir $(MKFILE_PATH))
SOLC_BIN       := $(CURRENT_DIR)/build/solc-static-linux


all: $(SOLC_BIN) $(MODULES)


$(SOLC_BIN):
	mkdir -p $(dir $(SOLC_BIN)) && \
	curl -fsSL -o $(SOLC_BIN) \
		https://github.com/ethereum/solidity/releases/download/$(SOLC_VERSION)/solc-static-linux \
		&& \
	chmod +x $(SOLC_BIN)


solc_bin: $(SOLC_BIN)


$(MODULES):
	$(MAKE) -C $@


$(addprefix clean_,$(MODULES)):
	$(MAKE) -C $(subst clean_,,$@) clean


clean: $(addprefix clean_,$(MODULES))
	rm -rf $(SOLC_BIN)


.PHONY: all clean solc_bin $(MODULES) $(addprefix clean_,$(MODULES))
