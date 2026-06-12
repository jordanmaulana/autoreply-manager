ARCH := $(shell uname -m)

upgrade:
	uv sync
	uv lock --upgrade
	uv sync --frozen --no-install-project

audit:
	cd frontend && pnpm audit fix

lint:
	uv run ruff format .
	uv run ruff check . --fix

dev:
	uv run manage.py runserver 8000

# Host port 15432 to avoid clashing with native Postgres on 5432/5433
db:
	docker run -d --name arm-pg -p 15432:5432 \
		-e POSTGRES_DB=app -e POSTGRES_USER=app -e POSTGRES_PASSWORD=app \
		-v arm-pgdata:/var/lib/postgresql/data pgvector/pgvector:pg16

poller:
	uv run manage.py poll_threads

mmg:
	uv run manage.py makemigrations

migrate:
	uv run manage.py migrate

tw-run:
	npx @tailwindcss/cli -i ./static/input.css -o ./static/output.css --watch

tw-build:
	npx @tailwindcss/cli -i ./static/input.css -o ./static/output.css

web:
	cd frontend && pnpm run dev

dock:
	docker compose --env-file .env.docker down
	docker compose --env-file .env.docker build
	docker compose --env-file .env.docker up -d
	docker compose --env-file .env.docker logs -f
