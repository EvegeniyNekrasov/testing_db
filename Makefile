PY=python3
PIP=pip3

init:
	@if [ ! -f .env ]; then cp .env.example .env; fi
	$(PIP) install -r requirements.txt

up:
	docker compose up -d

down:
	docker compose down

psql:
	docker exec -it pg17_app psql -U $$(grep POSTGRES_USER .env | cut -d '=' -f2) -d $$(grep POSTGRES_DB .env | cut -d '=' -f2)

seed:
	$(PY) src/seed_database.py

