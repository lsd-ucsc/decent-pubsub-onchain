MODULE_NAME := tests
CONTRACTS   := \
	HelloWorldPublisher \
	HelloWorldSubscriber


all:    $(addprefix ../build/$(MODULE_NAME)/,$(addsuffix .abi,$(CONTRACTS))) \
		$(addprefix ../build/$(MODULE_NAME)/,$(addsuffix .bin,$(CONTRACTS))) \
		$(addprefix ../build/$(MODULE_NAME)/,checksums.txt)


../build/nodeenv.state:
	$(MAKE) -C .. build/nodeenv.state


../build/$(MODULE_NAME)/%.bin: %.sol ../build/nodeenv.state
	. ../build/nodeenv/bin/activate; \
	solcjs  --optimize --optimize-runs 200 \
			--bin \
			--include-path node_modules/ --base-path .. \
			--output-dir ../build/$(MODULE_NAME)/ \
			$< && \
	mv  ../build/$(MODULE_NAME)/$(MODULE_NAME)_$(basename $<)_sol_$(basename $<).bin \
		../build/$(MODULE_NAME)/$(basename $<).bin && \
	rm  -f ../build/$(MODULE_NAME)/*_sol_*.bin; \
	deactivate_node


../build/$(MODULE_NAME)/%.abi: %.sol ../build/nodeenv.state
	. ../build/nodeenv/bin/activate; \
	solcjs  --optimize --optimize-runs 200 \
			--abi \
			--include-path node_modules/ --base-path .. \
			--output-dir ../build/$(MODULE_NAME)/ \
			$< && \
	mv  ../build/$(MODULE_NAME)/$(MODULE_NAME)_$(basename $<)_sol_$(basename $<).abi \
		../build/$(MODULE_NAME)/$(basename $<).abi && \
	rm  -f ../build/$(MODULE_NAME)/*_sol_*.abi; \
	deactivate_node


../build/$(MODULE_NAME)/checksums.txt:  $(addprefix ../build/$(MODULE_NAME)/,$(addsuffix .abi,$(CONTRACTS))) \
										$(addprefix ../build/$(MODULE_NAME)/,$(addsuffix .bin,$(CONTRACTS)))
	( \
		cd ../build/$(MODULE_NAME); \
		sha256sum $(addsuffix .abi,$(CONTRACTS)) $(addsuffix .bin,$(CONTRACTS)) > checksums.txt; \
	)


checksums: ../build/$(MODULE_NAME)/checksums.txt


clean:
	rm -f   $(addprefix ../build/$(MODULE_NAME)/,$(addsuffix .abi,$(CONTRACTS))) \
			$(addprefix ../build/$(MODULE_NAME)/,$(addsuffix .bin,$(CONTRACTS))) \
			$(addprefix ../build/$(MODULE_NAME)/,checksums.txt)


.PHONY: all clean checksums
