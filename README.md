# Taxicifra

Aplicación web para que un taxista autónomo controle la economía de su negocio: gastos (tickets con OCR/IA), ingresos, kilometraje y dashboard de beneficio y coste por kilómetro.

Proyecto Intermodular de DAM. La especificación completa está en [AGENTS.md](AGENTS.md).

## Tecnologías

- **Backend:** Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL 16
- **Seguridad:** contraseñas con argon2 y autenticación con JWT
- **Frontend (pendiente):** React, TypeScript y Tailwind CSS
- **Entorno:** Docker Compose, pytest y ruff

## Estado actual

| Módulo | Backend | Frontend |
| --- | --- | --- |
| Autenticación (registro y login) | Hecho | Pendiente |
| Vehículos | Hecho | Pendiente |
| Tickets y OCR | En curso (gestión manual y confirmación completas; falta foto y OCR) | Pendiente |
| Ingresos | Pendiente | Pendiente |
| Kilometraje | Pendiente | Pendiente |
| Dashboard | Pendiente | Pendiente |

Endpoints disponibles (prefijo `/api/v1`):

| Método | Ruta | Descripción | Requiere token |
| --- | --- | --- | --- |
| POST | `/auth/register` | Registrar un usuario | No |
| POST | `/auth/login` | Iniciar sesión y obtener el token JWT | No |
| GET | `/vehicles` | Listar los vehículos del usuario | Sí |
| POST | `/vehicles` | Dar de alta un vehículo | Sí |
| PUT | `/vehicles/{id}` | Editar un vehículo | Sí |
| DELETE | `/vehicles/{id}` | Eliminar un vehículo | Sí |
| GET | `/tickets` | Listar tickets con filtros (fechas, categoría, estado, vehículo) y paginación | Sí |
| POST | `/tickets` | Crear un ticket a mano (nace pendiente de revisión) | Sí |
| GET | `/tickets/{id}` | Consultar un ticket | Sí |
| PUT | `/tickets/{id}` | Editar un ticket (vuelve a pendiente de revisión) | Sí |
| DELETE | `/tickets/{id}` | Eliminar un ticket | Sí |
| POST | `/tickets/{id}/confirm` | Confirmar un ticket (campos completos y base + IVA = total, ±0,02 €) | Sí |

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

## Probar la API desde Swagger

1. Abre http://localhost:8000/docs.
2. Crea un usuario con `POST /api/v1/auth/register` (la contraseña necesita al menos 8 caracteres).
3. Inicia sesión con `POST /api/v1/auth/login` y copia el `access_token` de la respuesta.
4. Pulsa **Authorize**, pega el token y confirma. A partir de ahí puedes usar los endpoints protegidos.

## Tests

```bash
docker compose exec backend pytest
```

Los tests se ejecutan dentro del contenedor contra una base de datos PostgreSQL aparte (`<POSTGRES_DB>_test`), que se crea automáticamente. Cada test se deshace al terminar, así que no dejan datos ni tocan la base de datos de desarrollo.

## Estructura del backend

```text
backend/
├── app/
│   ├── main.py        # aplicación FastAPI y manejo uniforme de errores
│   ├── core/          # configuración, seguridad (hash y JWT) y errores
│   ├── api/           # rutas (sin lógica de negocio) y dependencias
│   ├── schemas/       # validación de entrada y salida (Pydantic)
│   ├── services/      # lógica de negocio y acceso a datos
│   ├── models/        # entidades SQLAlchemy
│   └── db/            # conexión y migraciones de Alembic
└── tests/
```

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
