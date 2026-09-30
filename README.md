# TaxiGest

Aplicación web para que un taxista autónomo controle la economía de su negocio: gastos (tickets con OCR/IA), ingresos, kilometraje y dashboard de beneficio y coste por kilómetro.

Proyecto Intermodular de DAM. La especificación completa está en [AGENTS.md](AGENTS.md).

## Requisitos

- Docker y Docker Compose

## Arrancar en local

```bash
cp .env.example .env        # y cambia la contraseña de PostgreSQL
docker compose up --build
```

- API: http://localhost:8000
- Documentación Swagger: http://localhost:8000/docs

Al arrancar, el backend aplica automáticamente las migraciones pendientes (`alembic upgrade head`).

## Comandos útiles

```bash
docker compose exec backend pytest                                 # tests
docker compose exec backend ruff check .                           # linter
docker compose exec backend ruff format .                          # formateo
docker compose exec backend alembic revision --autogenerate -m "…" # nueva migración
docker compose down                                                # parar (conserva datos)
docker compose down -v                                             # parar y BORRAR datos
```
