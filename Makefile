help:
	@echo "Usage:"
	@echo "    make help             prints this help."
	@echo "    make compile          compile prod & dev requirements from their specs."
	@echo "    make deploy           deploy the project."
	@echo "    make fix              fix formatting and import sort ordering."
	@echo "    make format           run the format checker (black)."
	@echo "    make lint             run the linter (flake8)."
	@echo "    make run              run the dev server."
	@echo "    make setup            set up/update the local dev env."
	@echo "    make sort             run the sort checker (isort)."
	@echo "    make test             run the test suite."

.PHONY: compile
compile:
	pip-compile --generate-hashes requirements.in -o requirements.txt
	pip-compile --generate-hashes requirements.dev.in -o requirements.dev.txt

.PHONY: deploy
deploy:
	git push dokku main

.PHONY: fix
fix:
	black .
	isort .

.PHONY: format
format:
	@echo "Running black" && \
		black --check . \
		|| exit 1

.PHONY: lint
lint:
	@echo "Running flake8" && \
		flake8 \
		|| exit 1

.PHONY: run
run:
	python manage.py runserver

.PHONY: setup
setup:
	pip install --require-hashes -r requirements.dev.txt
	pre-commit install

.PHONY: sort
sort:
	@echo "Running isort" && \
		isort --check-only --diff . \
		|| exit 1

.PHONY: test
test:
	python manage.py collectstatic --no-input && \
	pytest --cov=jobserver --cov=services --cov=tests


.PHONY: dev-config
dev-config:
	cp dotenv-sample .env
	./scripts/dev-env.sh .env
