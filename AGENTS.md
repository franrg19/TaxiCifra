# AGENTS.md — Taxicifra

Fuente de verdad ÚNICA del proyecto. Cualquier IA (Claude Code u otra) que trabaje en este repositorio debe leerlo ENTERO antes de tocar código y ceñirse a él.

---

## 0. Reglas de oro

1. **Este documento manda.** Si una petición, un comentario del código o tu propio criterio contradicen este fichero, NO implementes: avisa a Fran y pregunta.
2. **No inventes requisitos.** Si algo no está definido aquí, pregunta. Si está en la sección 15 (decisiones abiertas), usa la propuesta indicada y dilo explícitamente.
3. **No añadas nada que no esté aquí:** ni funcionalidades, ni endpoints, ni tablas, ni campos, ni capas, ni dependencias. Lo que está en la sección 3 como "FUERA DEL MVP" NO se implementa.
4. **Solo Fran cambia los requisitos**, editando este fichero. Puedes proponer cambios, pero no aplicarlos por tu cuenta.
5. **SIMPLICIDAD ante todo.** Entre dos soluciones que cumplen el requisito, elige la más simple. Sin abstracciones "por si acaso".
6. **El flujo OCR (subida → revisión → confirmación) es el núcleo del proyecto.** Es lo último que se recorta.

## 1. Proyecto

**Taxicifra** es una aplicación web para que un taxista autónomo controle la economía de su negocio: registra gastos fotografiando tickets (OCR/IA), registra ingresos y kilometraje, y ve en un dashboard su beneficio estimado y su coste por kilómetro.

- Es el **Proyecto Intermodular de DAM**. El proyecto debe estar **prácticamente finalizado el 20 de noviembre de 2026**, el **depósito final es el 7 de diciembre de 2026** y la **defensa es la semana del 14 de diciembre de 2026**. Desarrollador único: Fran.
- **Regla de diseño clave:** los datos extraídos por OCR/IA NUNCA son definitivos hasta que el usuario los revisa y confirma.

## 2. Cómo trabajar con Fran

- **Habla en español.** Identificadores de código en inglés (ver sección 11).
- **Pasos pequeños y modulares.** Una tarea o un módulo cada vez. Antes de tocar varios ficheros, lista cuáles vas a tocar y por qué.
- **Al terminar cada paso:** resume en 2-3 líneas qué hiciste, cómo ejecutarlo o probarlo, y PREGUNTA si continúas con el siguiente. No encadenes varios pasos sin confirmación.
- **Ejemplos de código concretos**, no descripciones vagas.
- **Explica el porqué de forma breve.** Fran es junior: tras escribir código, explica qué hace cada fichero. Sin comparaciones con Java/Spring.
- **Git lo maneja Fran.** No hagas commits, push ni merges: deja los cambios sin commitear y propón el mensaje y los comandos. Se trabaja con una rama por módulo o tarea (`feature/...`, `fix/...`, `docs/...`) y Pull Request hacia `main`.
- **Todo cambio de comportamiento lleva su test** (sección 12).
- Si Fran te pide algo que rompe una regla de este documento, díselo con claridad y propón la alternativa que sí encaja.

## 3. Alcance

### DENTRO del MVP (todo esto se implementa)

- Registro e inicio de sesión (JWT).
- Gestión de vehículos (matrícula, marca, modelo).
- Tickets: creación manual, subida de foto con OCR/IA, revisión, corrección, confirmación, filtros, paginación, edición y borrado.
- Ingresos: alta, consulta, edición y borrado, con filtros y paginación.
- Kilometraje: lecturas del cuentakilómetros por vehículo.
- Dashboard: gastos, ingresos, beneficio estimado, gasto por categoría, evolución mensual, número de tickets, kilómetros recorridos y coste por kilómetro.

### FUERA del MVP (NO implementar, ni "preparar el terreno")

Informes PDF/Excel · recordatorios de mantenimiento · documentación del vehículo · predicción de gastos · asistente conversacional · roles o flotas (varios conductores por cuenta) · app móvil/PWA · almacenamiento de imágenes en la nube · despliegue automático · microservicios · colas o procesamiento asíncrono.

## 4. Stack (CERRADO, no cambiar sin aprobación de Fran)

| Capa                       | Tecnología                                 |
| -------------------------- | ------------------------------------------ |
| Backend                    | Python + FastAPI                           |
| ORM                        | SQLAlchemy, **modo síncrono**              |
| Base de datos              | PostgreSQL                                 |
| Migraciones                | Alembic                                    |
| Autenticación              | JWT + hash de contraseña con argon2        |
| Validación y configuración | Pydantic + pydantic-settings               |
| Frontend                   | React + TypeScript + Tailwind CSS          |
| Tests                      | pytest (backend), Vitest (frontend, pocos) |
| Contenedores               | Docker + Docker Compose                    |
| CI                         | GitHub Actions                             |

**Por qué Python/FastAPI** (para la memoria): productividad (Swagger automático, validación con Pydantic) y ecosistema de IA/OCR más maduro.

**NO uses:** SQLAlchemy async, Django, Flask, ORMs alternativos, librerías de estado global pesadas en el frontend, ni ninguna dependencia que no esté aquí sin preguntar antes.

**Librerías concretas ya aprobadas (backend):** `uvicorn` (servidor), `psycopg` (driver de PostgreSQL), `argon2-cffi` (hash), `PyJWT` (tokens), `email-validator` (validación de emails), `python-multipart` (subida de ficheros), `httpx` (cliente de los tests) y `ruff` (linter y formateo).

## 5. Arquitectura

Cliente-servidor con API REST. **Monolito modular.**

```text
React + TypeScript  ──HTTPS/REST (JSON)──►  FastAPI  ──►  PostgreSQL
                                               │
                                               ├──►  Volumen local de imágenes
                                               └──►  Proveedor OCR/IA (tras una interfaz)
```

### Estructura del backend

```text
backend/app/
├── main.py
├── core/
│   ├── config.py          # pydantic-settings
│   ├── errors.py          # ApiError (error de negocio con code)
│   └── security.py        # hash de contraseñas y JWT
├── api/
│   ├── deps.py            # get_db, get_current_user
│   └── v1/
│       ├── auth.py
│       ├── vehicles.py
│       ├── tickets.py
│       ├── incomes.py
│       ├── odometer.py
│       └── dashboard.py
├── models/                # entidades SQLAlchemy
├── schemas/               # esquemas Pydantic
├── services/
│   ├── auth_service.py
│   ├── vehicle_service.py
│   ├── ticket_service.py
│   ├── income_service.py
│   ├── odometer_service.py
│   ├── dashboard_service.py
│   └── ocr/
│       ├── base.py        # interfaz OcrProvider + ExtractedTicket
│       ├── fake.py        # FakeOcrProvider
│       └── <proveedor>.py # proveedor real (se decide en la semana 3)
└── db/
    ├── database.py
    └── migrations/
```

### Reglas de capas

- **Routes (`api/`)**: reciben la petición, llaman a un service y devuelven la respuesta. SIN lógica de negocio y SIN consultas a la base de datos.
- **Schemas**: validan entrada y salida.
- **Services**: lógica de negocio y acceso a datos con la **sesión de SQLAlchemy directamente**. **NO existe capa `repositories/`. No la crees.**
- **Models**: solo definición de entidades.
- **El proveedor OCR solo se usa a través de la interfaz `OcrProvider`.** Ningún service importa un proveedor concreto.

### Estructura del frontend (PROVISIONAL, se fija en la semana 1)

```text
frontend/src/
├── api/          # cliente HTTP tipado hacia /api/v1
├── components/
├── pages/        # login, vehículos, tickets, revisión de ticket, ingresos, kilometraje, dashboard
└── types/
```

## 6. Modelo de datos

Importes: `Numeric(10, 2)` / `Decimal`. **NUNCA `float`.** Moneda: euros.

**User**: id, name, email (único), password_hash, created_at

**Vehicle**: id, user_id (FK, índice), plate, brand, model, created_at. Único `(user_id, plate)`.

**Ticket**: id, user_id (FK, índice), vehicle_id (FK, opcional), date (índice), vendor, category, net_amount, vat, total, image_path, ocr_text, status (`pending_review` | `confirmed`), created_at

**Income**: id, user_id (FK, índice), vehicle_id (FK, opcional), date (índice), amount, description, created_at

**OdometerReading**: id, user_id (FK, índice), vehicle_id (FK), date, odometer_km (entero), created_at

Índices: `tickets(user_id, date)`, `incomes(user_id, date)`, `odometer_readings(vehicle_id, date)`, `users(email)` único.

**No existe la entidad Gasto.** Un gasto es un ticket con `status = confirmed`.

**Categorías de ticket:** `combustible`, `mantenimiento`, `seguro`, `limpieza`, `reparaciones`,`emisora`,`autonomo`,`datafono`, `otros`.

Todo cambio de esquema pasa por una migración de Alembic. NUNCA modifiques la base de datos a mano.

## 7. Reglas de negocio

### Tickets

- Un ticket nace en `pending_review` (por foto o manual) y pasa a `confirmed` solo con `POST /tickets/{id}/confirm`.
- En `pending_review`, los campos de contenido pueden estar vacíos. Para confirmar deben estar completos: `date`, `vendor`, `category`, `net_amount`, `vat`, `total`.
- Al confirmar se valida `net_amount + vat ≈ total` (tolerancia de 0,02 €). Si no cuadra, se avisa al usuario con un error claro.
- Si el OCR falla, el ticket se crea igualmente en `pending_review` con los campos vacíos y la imagen guardada. El fallo del OCR NUNCA bloquea al usuario.
- Un `vehicle_id` recibido debe pertenecer al usuario autenticado.

### Vehículos

- Un usuario puede tener varios. Matrícula única por usuario.
- Un vehículo con tickets, ingresos o lecturas asociados NO se elimina sin confirmación explícita: `DELETE /vehicles/{id}` responde `409` con código de error. Con `?force=true` se borra el vehículo y sus lecturas de km, y los tickets e ingresos SE CONSERVAN con `vehicle_id = null`. NUNCA se borran tickets ni ingresos por borrar un vehículo.

### Kilometraje

- Una lectura no puede ser inferior a la lectura anterior del mismo vehículo.
- Km recorridos en un periodo = última lectura − primera lectura del periodo.
- Sin filtro de vehículo, los km recorridos son la SUMA de los km de cada vehículo (cada uno con su última − primera lectura del periodo). Un vehículo con menos de dos lecturas en el periodo no suma.

### Dashboard

Para un periodo y, opcionalmente, un vehículo:

- Gasto total = suma de `total` de tickets `confirmed`. Los `pending_review` NUNCA cuentan.
- Ingresos totales = suma de `amount`.
- **Beneficio estimado = ingresos − gastos confirmados.**
- **Coste por km = gastos confirmados / km recorridos.**
- Sin al menos dos lecturas en el periodo, el coste por km es "sin datos" (`null`). NUNCA error ni división por cero.
- Las agregaciones se hacen en SQL (`GROUP BY`), NO en Python.

## 8. API

Prefijo `/api/v1`. Listados paginados (`page` desde 1, `size` por defecto 20, máximo 100). Errores con formato uniforme: `{"detail": "...", "code": "..."}`.

```text
POST   /auth/register
POST   /auth/login

GET    /vehicles
POST   /vehicles
PUT    /vehicles/{id}
DELETE /vehicles/{id}

GET    /tickets          ?page&size&date_from&date_to&category&status&vehicle_id
POST   /tickets          (creación manual)
POST   /tickets/upload   (multipart: imagen + OCR síncrono)
GET    /tickets/{id}
GET    /tickets/{id}/image   (foto del ticket, solo su dueño)
PUT    /tickets/{id}
DELETE /tickets/{id}
POST   /tickets/{id}/confirm

GET    /incomes          ?page&size&date_from&date_to&vehicle_id
POST   /incomes
PUT    /incomes/{id}
DELETE /incomes/{id}

GET    /vehicles/{id}/odometer
POST   /vehicles/{id}/odometer
DELETE /vehicles/{id}/odometer/{reading_id}

GET    /dashboard/summary       ?date_from&date_to&vehicle_id
GET    /dashboard/by-category   ?date_from&date_to&vehicle_id
GET    /dashboard/monthly       ?year&vehicle_id
```

`dashboard/summary` devuelve: gastos, ingresos, beneficio, número de tickets, km recorridos y coste por km.

## 9. Flujo OCR/IA

Flujo **SÍNCRONO**, una sola petición:

`POST /tickets/upload` → valida tipo real (JPG/PNG) y tamaño (máx. 5 MB) → guarda la imagen en el volumen local (en BD solo `image_path`) → llama al proveedor → crea el ticket `pending_review` → el usuario corrige con `PUT` → confirma con `POST .../confirm`.

Interfaz obligatoria:

```python
# services/ocr/base.py
import datetime as dt
from decimal import Decimal
from typing import Protocol
from pydantic import BaseModel

class ExtractedTicket(BaseModel):
    date: dt.date | None = None  # dt.date: el campo "date" taparía al tipo date
    vendor: str | None = None
    net_amount: Decimal | None = None
    vat: Decimal | None = None
    total: Decimal | None = None
    category: str | None = None

class OcrProvider(Protocol):
    def extract(self, image: bytes, mime_type: str) -> ExtractedTicket: ...
```

- Se desarrolla PRIMERO con `FakeOcrProvider` (datos fijos). Los tests usan SIEMPRE el fake.
- El proveedor real se decide en la **semana 3**, tras probar 10-15 fotos reales. Hasta entonces NO integres ninguno.
- La clave de API va en variable de entorno. NUNCA en el código ni en el repositorio.

## 10. Seguridad (obligatorio)

- **Autorización a nivel de recurso:** TODA consulta filtra por el usuario autenticado. Si el recurso no es suyo, responde **404** (no 403).
- Contraseñas con **argon2**. JWT con caducidad de **24 horas** (decisión de Fran: comodidad durante toda la jornada, sin refresh token) y algoritmo fijado explícitamente. Al ser una caducidad larga, el token viaja SIEMPRE por HTTPS y NUNCA se registra en logs.
- Validar toda entrada con Pydantic. Validar archivos subidos por tipo real, no solo extensión.
- CORS restringido al origen del frontend.
- Secretos por variables de entorno con `pydantic-settings`. `.env` en `.gitignore`; se versiona un `.env.example` sin secretos.
- RGPD: tickets, ingresos y km son datos personales. Minimización, acceso solo del propietario y posibilidad de borrar los propios datos. Las imágenes enviadas a un proveedor externo deben constar en la documentación.

## 11. Convenciones de código

- **Identificadores en inglés** (variables, funciones, clases, tablas, campos, endpoints). **Comentarios, docstrings y textos de interfaz en español.**
- Tipado en todo el backend (type hints) y TypeScript estricto en el frontend. Sin `any` salvo justificación.
- Funciones cortas, un propósito. Nada de código muerto ni comentado.
- Errores de negocio con `ApiError` (subclase de `HTTPException` definida en `core/errors.py`, con `status_code`, `detail` y `code`). Los manejadores de `main.py` devuelven TODOS los errores con el formato de la sección 8, también los de validación (422, con `detail` del tipo `campo: motivo`).
- Ejemplo de comprobación de propiedad (el patrón a seguir):

```python
def get_ticket_or_404(db: Session, ticket_id: int, user_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket or ticket.user_id != user_id:
        raise ApiError(status_code=404, detail="Ticket no encontrado", code="ticket_not_found")
    return ticket
```

- Commits pequeños, uno por cambio lógico, con mensaje en español en imperativo (`Añadir endpoint de confirmación de tickets`).

## 12. Testing

- **Backend (pytest):** unitarios de services · validaciones (`net + vat ≈ total`, lectura de km no decreciente) · endpoints y autenticación · **autorización (un usuario NO puede leer ni tocar recursos de otro)** · cálculos del dashboard, incluido el caso "sin datos" · integración con BD · flujo OCR con `FakeOcrProvider`.
- **Frontend (Vitest):** unas pocas pruebas sobre el formulario de revisión de tickets. No más.
- Un cambio no está terminado si los tests no pasan.

## 13. Entorno y CI

- **Docker Compose:** FastAPI + PostgreSQL, con volúmenes para datos de BD e imágenes. El frontend corre con Node/Vite en desarrollo.
- **GitHub Actions** en cada push/PR: instalar dependencias → linter y formateo → tests → build.
- Todo debe arrancar con `docker compose up` sin pasos manuales ocultos. Documenta en el `README` cualquier comando nuevo.

## 14. Plan y prioridades

| Semana      | Objetivo                                                                                    |
| ----------- | ------------------------------------------------------------------------------------------- |
| 1           | Requisitos (RFTP) y casos de uso, E-R, contrato API, repo con Docker Compose                |
| 2           | Auth (registro, login, JWT) y vehículos                                                     |
| 3           | CRUD de tickets, autorización, filtros y paginación; elegir proveedor OCR                   |
| 4           | Subida de imagen, OCR, estados y confirmación                                               |
| 5           | Ingresos, kilometraje y endpoints del dashboard                                             |
| 6           | Frontend: login, vehículos, tickets                                                         |
| 7           | Frontend: subida y revisión, ingresos, kilometraje                                          |
| 8           | Frontend: dashboard y prueba completa → **MVP cerrado el 20/11**                            |
| 9 y margen  | CI (GitHub Actions), tests de frontend, pulido, memoria y README. **Depósito final: 07/12** |
| 08/12–13/12 | Ensayo de la defensa y preparación de la demo. **Defensa: semana del 14/12**                |

**Orden de recorte si el tiempo aprieta:** tests de frontend → CI/CD → coste por km y kilometraje → asociación a vehículo de tickets e ingresos → evolución mensual. **El flujo OCR NUNCA se recorta.**

Trabaja siempre en el orden de las semanas. No adelantes módulos de semanas posteriores sin que Fran lo pida.

## 15. Decisiones

### Cerradas (Fran las ha decidido; NO las cambies)

| Tema                                            | Decisión                                                                             |
| ----------------------------------------------- | ------------------------------------------------------------------------------------ |
| Algoritmo de hash                               | argon2                                                                               |
| Caducidad del JWT                               | 24 horas, sin refresh token                                                          |
| Borrado de vehículo con datos asociados         | `409`, salvo `?force=true` (ver sección 7)                                           |
| Km recorridos sin filtro y con varios vehículos | Sumar los km de cada vehículo                                                        |
| Paginación                                      | `size` por defecto 20, máximo 100                                                    |
| Tolerancia de `net + vat ≈ total`               | 0,02 €                                                                               |
| Versión de Python                               | 3.12                                                                                 |
| Proveedor OCR/IA real                           | Se decide en la semana 3. Hasta entonces NO integrar ninguno: usar `FakeOcrProvider` |

### Tomadas durante el desarrollo (aprobadas por Fran; NO las cambies)

| Tema                 | Decisión                                                                                                                                                                                                                                                     |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Contraseña           | Mínimo 8 caracteres (máximo 128)                                                                                                                                                                                                                             |
| Email                | Se guarda en minúsculas; el registro y el login no distinguen mayúsculas                                                                                                                                                                                     |
| Matrícula            | Se guarda en mayúsculas y sin espacios ni guiones (`1234 abc` = `1234ABC`). Máximo 15 caracteres; marca y modelo, 50                                                                                                                                         |
| JWT                  | Algoritmo HS256. El token lleva `sub` (id de usuario) y `exp`. Clave en la variable `JWT_SECRET` (obligatoria, sin valor por defecto)                                                                                                                        |
| Login                | Entrada JSON (`email`, `password`); salida `{"access_token", "token_type": "bearer"}`. Email inexistente y contraseña incorrecta devuelven el mismo `401` (`invalid_credentials`)                                                                            |
| Códigos de respuesta | `201` altas · `204` borrados · `401` sin token válido (`not_authenticated`) · `404` recurso inexistente o ajeno · `409` duplicados (`email_already_registered`, `plate_already_registered`) · `422` validación (`validation_error`)                          |
| `GET /vehicles`      | Sin paginación (devuelve todos los vehículos del usuario)                                                                                                                                                                                                    |
| Borrado de vehículo | Con tickets o ingresos asociados responde `409` (`vehicle_has_related_data`); con `?force=true` se borra y sus tickets e ingresos quedan con `vehicle_id = null` (claves foráneas `ON DELETE SET NULL`). Hecho para tickets e ingresos; falta ampliarlo a lecturas de km (se borran con el vehículo) |
| Tests del backend    | Se ejecutan en Docker contra una base de datos aparte (`<nombre>_test`), creada automáticamente; cada test se deshace con un rollback                                                                                                                        |
| Endpoint `/auth/me`  | No existe. Se decidirá en la semana 6 si el frontend lo necesita                                                                                                                                                                                             |
| Memoria              | Sigue la plantilla del centro: RFTP y casos de uso (no historias de usuario). El contrato de la API no se incluye en la memoria (lo documenta Swagger)                                                                                                       |
| Planificación        | Inicio de auth (tabla `users` y registro) adelantado a la semana 1 a petición de Fran                                                                                                                                                                        |
| Nombre del proyecto  | **Taxicifra** (antes TaxiGest; cambiado el 06/10/2026 porque ya existe una app con ese nombre para el mismo público). Solo cambia el nombre visible: la carpeta, la base de datos, el usuario de PostgreSQL y los nombres de Docker siguen siendo `taxigest` |
| Alta de tickets | Todos los campos de contenido son opcionales al crear (borrador). Importes ≥ 0 con dos decimales como máximo; `vendor` hasta 100 caracteres. El cliente no puede fijar el estado: todo ticket nace en `pending_review`. Estado y categoría se guardan como texto validado (no como `ENUM` de PostgreSQL) |
| Listado de tickets | Respuesta paginada con la forma `{"items", "total", "page", "size"}` (esquema genérico `Page[T]`, reutilizable en ingresos). Orden: fecha descendente, sin fecha al final. `page` ≥ 1 y `size` entre 1 y 100; fuera de rango → `422`. Fechas inclusivas. Un `vehicle_id` ajeno en el filtro devuelve lista vacía |
| Edición de tickets | `PUT /tickets/{id}` reemplaza todos los campos y deja SIEMPRE el ticket en `pending_review`, aunque estuviera confirmado. La edición no valida importes: solo lo hace la confirmación. Recurso inexistente o ajeno → `404` (`ticket_not_found`) |
| Confirmación de tickets | `POST /tickets/{id}/confirm` sin cuerpo; confirma el ticket tal como está guardado. Si faltan campos → `422` (`ticket_incomplete`) indicando TODOS los que faltan; si la diferencia entre `net_amount + vat` y `total` supera 0,02 € → `422` (`amounts_mismatch`) con los importes. Si falla, el ticket sigue en `pending_review`. Confirmar un ticket ya confirmado devuelve `200` (idempotente) |
| Subida de tickets por foto | Tipo real por los primeros bytes (firma de JPG o PNG), no por la extensión: si no es JPG ni PNG → `415` (`unsupported_image_type`); más de 5 MB → `413` (`image_too_large`). La imagen se guarda con un nombre aleatorio (`uuid4` + extensión), nunca el del usuario, y en BD solo va ese nombre (`image_path`). Se guarda ANTES de llamar al OCR. La subida no lleva `vehicle_id` (se asigna al revisar con `PUT`). `ocr_text` queda vacío hasta elegir el proveedor real. Librería `python-multipart` aprobada para recibir ficheros |
| Tolerancia a fallos del OCR | Cualquier error del proveedor se registra en el log y el ticket se crea con los campos vacíos. Lo que devuelve el OCR se valida con las mismas reglas que el alta manual (`TicketCreate`): los campos inválidos (categoría inexistente, importe negativo, con más de dos decimales o demasiado grande, `vendor` vacío o de más de 100 caracteres) se dejan vacíos y se conserva el resto. El proveedor se obtiene con `get_ocr_provider()` en `api/deps.py` (hoy `FakeOcrProvider`) |
| Imagen de un ticket | `GET /tickets/{id}/image` devuelve el fichero solo a su dueño (ticket ajeno o inexistente → `404` `ticket_not_found`; ticket sin foto o fichero ausente en disco → `404` `image_not_found`). La carpeta de imágenes NO se publica como estáticos. `DELETE /tickets/{id}` borra también la foto, después del `commit` (RGPD y sin ficheros huérfanos) |
| Ingresos | `date` y `amount` obligatorios; `amount` > 0 con dos decimales como máximo; `description` opcional, de 1 a 255 caracteres. `vehicle_id` ajeno → `404`. Listado igual que el de tickets (`Page[T]`, orden por fecha descendente, fechas inclusivas, vehículo ajeno → lista vacía). `PUT` reemplaza todos los campos con las mismas reglas que el alta. Sin `GET /incomes/{id}` (no está en la sección 8). Ingreso inexistente o ajeno → `404` (`income_not_found`). La paginación (`page`, `size`) se define una sola vez en `PageParams` |

### Abiertas

Son de semanas posteriores y no bloquean nada ahora. Hasta que Fran las cierre, usa la **propuesta** indicada, dilo explícitamente y déjala fácil de cambiar.

| Tema                               | Propuesta por defecto                        |
| ---------------------------------- | -------------------------------------------- |
| Linter y formateo                  | ruff (backend), ESLint + Prettier (frontend) |
| Librería de gráficos del dashboard | Recharts                                     |
| Estructura del frontend            | La provisional de la sección 5               |

## 16. Prohibido

- Crear `repositories/`, usar SQLAlchemy async, o introducir colas, workers, Redis o microservicios.
- Usar `float` para dinero.
- Contar tickets `pending_review` como gasto.
- Guardar secretos o claves en el código o en el repositorio.
- Llamar a un proveedor OCR real en los tests.
- Devolver 403 para recursos de otro usuario (siempre 404).
- Calcular agregaciones del dashboard en Python.
- Implementar cualquier cosa de "FUERA del MVP".
- Cambiar este documento sin aprobación explícita de Fran.

## 17. Estado del proyecto (Fran lo actualiza)

- [x] Semana 1: requisitos (RFTP) y casos de uso, E-R, contrato API, repo base
- [x] Semana 2: auth y vehículos
- [ ] Semana 3: tickets CRUD + elegir proveedor OCR
- [ ] Semana 4: subida, OCR y confirmación
- [ ] Semana 5: ingresos, kilometraje y dashboard (backend)
- [ ] Semana 6: frontend (login, vehículos, tickets)
- [ ] Semana 7: frontend (subida y revisión, ingresos, km)
- [ ] Semana 8: frontend dashboard y prueba completa → MVP cerrado (20/11)
- [ ] Semana 9 y margen: CI, tests de frontend, pulido, memoria y README → depósito final (07/12)
- [ ] 08/12–13/12: ensayo de la defensa y demo → defensa (semana del 14/12)
