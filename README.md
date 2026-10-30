# Taxicifra

Aplicación web para que un taxista autónomo controle la economía de su negocio: gastos (tickets con OCR/IA), ingresos, kilometraje y dashboard de beneficio y coste por kilómetro.

Proyecto Intermodular de DAM. La especificación completa está en [AGENTS.md](AGENTS.md).

## Tecnologías

- **Backend:** Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL 16
- **Seguridad:** contraseñas con argon2 y autenticación con JWT
- **OCR/IA de tickets:** Claude Haiku 5.5 (API de Anthropic), con salidas estructuradas
- **Frontend:** React 19, TypeScript (estricto), Tailwind CSS 4 y React Router, con Vite
- **Entorno:** Docker Compose, pytest y ruff (backend); oxlint y Prettier (frontend)

## Estado actual

| Módulo | Backend | Frontend |
| --- | --- | --- |
| Autenticación (registro y login) | Hecho | Pendiente |
| Vehículos | Hecho | Pendiente |
| Tickets y OCR | Hecho (lectura de tickets con Claude; sin clave, OCR simulado) | Pendiente |
| Ingresos | Hecho | Pendiente |
| Kilometraje | Hecho | Pendiente |
| Dashboard | Hecho | Pendiente |

Endpoints disponibles (prefijo `/api/v1`):

| Método | Ruta | Descripción | Requiere token |
| --- | --- | --- | --- |
| POST | `/auth/register` | Registrar un usuario | No |
| POST | `/auth/login` | Iniciar sesión y obtener el token JWT | No |
| GET | `/vehicles` | Listar los vehículos del usuario | Sí |
| POST | `/vehicles` | Dar de alta un vehículo | Sí |
| PUT | `/vehicles/{id}` | Editar un vehículo | Sí |
| DELETE | `/vehicles/{id}` | Eliminar un vehículo | Sí |
| GET | `/vehicles/{id}/odometer` | Listar las lecturas de km de un vehículo (paginado, la más reciente primero) | Sí |
| POST | `/vehicles/{id}/odometer` | Registrar una lectura del cuentakilómetros (nunca por debajo de la anterior) | Sí |
| DELETE | `/vehicles/{id}/odometer/{reading_id}` | Eliminar una lectura de km | Sí |
| GET | `/tickets` | Listar tickets con filtros (fechas, categoría, estado, vehículo) y paginación | Sí |
| POST | `/tickets` | Crear un ticket a mano (nace pendiente de revisión) | Sí |
| POST | `/tickets/upload` | Crear un ticket a partir de su foto (JPG o PNG, máx. 5 MB), leída con OCR | Sí |
| GET | `/tickets/{id}` | Consultar un ticket | Sí |
| GET | `/tickets/{id}/image` | Ver la foto de un ticket (solo su dueño) | Sí |
| PUT | `/tickets/{id}` | Editar un ticket (vuelve a pendiente de revisión) | Sí |
| DELETE | `/tickets/{id}` | Eliminar un ticket | Sí |
| POST | `/tickets/{id}/confirm` | Confirmar un ticket (campos completos y base + IVA = total, ±0,02 €) | Sí |
| GET | `/incomes` | Listar ingresos con filtros (fechas, vehículo) y paginación | Sí |
| POST | `/incomes` | Registrar un ingreso (fecha e importe obligatorios) | Sí |
| PUT | `/incomes/{id}` | Editar un ingreso | Sí |
| DELETE | `/incomes/{id}` | Eliminar un ingreso | Sí |
| GET | `/dashboard/summary` | Resumen del periodo: gastos confirmados, ingresos, beneficio, nº de tickets, km y coste por km | Sí |
| GET | `/dashboard/by-category` | Gasto confirmado por categoría en un periodo, de mayor a menor | Sí |
| GET | `/dashboard/monthly` | Gastos, ingresos y beneficio de los 12 meses de un año (por defecto, el actual) | Sí |

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

### Lectura de tickets (OCR/IA)

Las fotos de los tickets se leen con un modelo de IA de Anthropic. Para activarlo, pon tu clave en `.env`:

```bash
ANTHROPIC_API_KEY=tu-clave        # se crea en https://console.anthropic.com
OCR_MODEL=claude-haiku-5-5       # opcional: otro modelo de Claude con visión
```

Sin clave, la aplicación funciona igual pero usa un **lector simulado** que devuelve siempre el mismo ticket (útil para probarla sin cuenta de Anthropic). Los tests usan siempre el lector simulado y nunca llaman a la API.

## Arrancar el frontend

Necesita [Node.js](https://nodejs.org) 20 o superior y el backend arrancado con Docker.

```bash
cd frontend
npm install        # solo la primera vez
npm run dev
```

- Aplicación: http://localhost:5173

En desarrollo, Vite reenvía las peticiones `/api` al backend (`localhost:8000`). Además, la API solo acepta llamadas de navegador desde el origen del frontend (CORS), configurable con la variable `FRONTEND_ORIGIN`.

Comandos del frontend (dentro de `frontend/`):

```bash
npm run lint           # linter (oxlint)
npm run format         # formatear con Prettier
npm run build          # comprobar tipos y generar la versión de producción
```

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
