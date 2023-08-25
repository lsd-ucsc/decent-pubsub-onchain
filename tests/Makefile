MODULE_NAME := tests
CONTRACTS   := \
	HelloWorldPublisher \
	HelloWorldSubscriber \
	BasicActionGasCost

MKFILE_PATH  := $(abspath $(lastword $(MAKEFILE_LIST)))
CURRENT_DIR  := $(dir $(MKFILE_PATH))
ROOT_DIR     := $(CURRENT_DIR)/..
BUILD_DIR    := $(ROOT_DIR)/build

SOLC_BIN     := $(BUILD_DIR)/solc-static-linux
OPTIMIZE_RUN := 200
SOLC_FLAGS   := --optimize --optimize-runs $(OPTIMIZE_RUN) \
				--revert-strings strip \
				--via-ir \
				--overwrite \
				--base-path $(ROOT_DIR) \
				--output-dir $(BUILD_DIR)/$(MODULE_NAME)/all/

CHECKSUM_BIN := openssl sha256


all: $(CONTRACTS) checksums


$(SOLC_BIN):
	$(MAKE) -C .. solc_bin


$(BUILD_DIR)/$(MODULE_NAME)/%.bin: %.sol $(SOLC_BIN)
	( \
		$(SOLC_BIN) --bin $(SOLC_FLAGS) $< && \
		cp  $(BUILD_DIR)/$(MODULE_NAME)/all/$(basename $<).bin \
			$(BUILD_DIR)/$(MODULE_NAME)/$(basename $<).bin \
	)


$(BUILD_DIR)/$(MODULE_NAME)/%.abi: %.sol $(SOLC_BIN)
	( \
		$(SOLC_BIN) --abi $(SOLC_FLAGS) $< && \
		cp  $(BUILD_DIR)/$(MODULE_NAME)/all/$(basename $<).abi \
			$(BUILD_DIR)/$(MODULE_NAME)/$(basename $<).abi \
	)


$(CONTRACTS): %: $(BUILD_DIR)/$(MODULE_NAME)/%.abi $(BUILD_DIR)/$(MODULE_NAME)/%.bin


$(BUILD_DIR)/$(MODULE_NAME)/checksums.txt: $(CONTRACTS)
	( \
		cd $(BUILD_DIR)/$(MODULE_NAME); \
		$(CHECKSUM_BIN) $(addsuffix .abi,$(CONTRACTS)) $(addsuffix .bin,$(CONTRACTS)) > checksums.txt; \
	)


checksums: $(BUILD_DIR)/$(MODULE_NAME)/checksums.txt


clean:
	rm -rf $(BUILD_DIR)/$(MODULE_NAME)/


.PHONY: all clean checksums $(CONTRACTS)
