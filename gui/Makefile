ACCOUNT?=$(shell cat ../ACCOUNT)
IMAGE=ledger-gui
VERSION?=dev
NAME=$(IMAGE)-$(ACCOUNT)

.PHONY: build shell image push

build:
	docker build . --build-arg BASE=$(BASE) -t $(ACCOUNT)/$(IMAGE):$(VERSION)

shell:
	-docker run -it --rm $(ACCOUNT)/$(IMAGE):$(VERSION) sh

image: build

push:
	docker push $(ACCOUNT)/$(IMAGE):$(VERSION)
