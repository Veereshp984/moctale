.PHONY: setup backend-setup frontend-setup backend-dev frontend-dev lint format test

setup: backend-setup frontend-setup

backend-setup:
	$(MAKE) -C backend install

frontend-setup:
	cd frontend && npm ci

backend-dev:
	$(MAKE) -C backend dev

frontend-dev:
	cd frontend && npm run dev

lint:
	$(MAKE) -C backend lint
	cd frontend && npm run lint

format:
	$(MAKE) -C backend format
	cd frontend && npm run format

test:
	$(MAKE) -C backend test
	cd frontend && npm test -- --run
