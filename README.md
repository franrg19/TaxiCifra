# TaxiGest

Aplicación web para que un taxista autónomo controle la economía de su negocio: gastos (tickets con OCR/IA), ingresos, kilometraje y dashboard de beneficio y coste por kilómetro.

Proyecto Intermodular de DAM. La especificación completa está en [AGENTS.md](AGENTS.md).

## Requisitos

- Docker y Docker Compose

## Arrancar en local

```bash
cp .env.example .env        # y cambia la contraseña de PostgreSQL y JWT_SECRET
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

## Entorno local para el editor (opcional)

Todo se ejecuta en Docker. El venv solo sirve para que el editor reconozca las librerías (autocompletado, sin imports en rojo).

```bash
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements-dev.txt
```

En VS Code: `Ctrl+Shift+P` → "Python: Select Interpreter" → `backend\.venv\Scripts\python.exe`.
Para activarlo a mano: `backend\.venv\Scripts\activate` (salir con `deactivate`).
