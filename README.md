# BookNest - Hotel Booking API

Django REST API for a Booking.com-like service: users, hotels, rooms, bookings, JWT auth, Redis-backed temporary data, and Swagger/OpenAPI docs.

## Tech Stack
- Python 3.12
- Django
- Django REST Framework
- drf-spectacular
- Simple JWT
- Redis
- Celery
- Docker Compose

## Environment File
Create a `.env` file from `.env.template` before starting:

```bash
cp .env.template .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.template .env
```

## Local Python Setup
### 1) Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```powershell
venv\Scripts\activate
```

### 2) Install dependencies
```bash
pip install -r requirements/local.txt
```

### 3) Run migrations
```bash
python manage.py migrate
```

### 4) Seed data manually if needed
```bash
python manage.py seed_data
```

### 5) Run the server
```bash
python manage.py runserver
```

## Docker Usage
The project uses helper scripts:
- [build.sh](/scripts/build.sh)
- [start.sh](/scripts/start.sh)

### What happens on startup
- Migrations run automatically in both `local` and `prod`
- `local` starts Django with `runserver`
- `prod` starts Django with `gunicorn`
- `local` runs `python manage.py seed_data` only on the first startup when the database is still empty

### Build only
```bash
./scripts/build.sh local build
./scripts/build.sh prod build
```

### Build and start
```bash
./scripts/build.sh local up
./scripts/build.sh prod up -d
```

### Windows PowerShell
If `./scripts/...` does not run directly, use Git Bash, WSL, or call it through `bash`:

```powershell
bash ./scripts/build.sh local up
bash ./scripts/build.sh prod up -d
```

### Environment Modes
- `local`: SQLite, development server, optional local Redis usage, auto-seeding on first empty startup
- `prod`: PostgreSQL profile, Gunicorn, production dependency set

### Useful Local Flags
From `.env`:

```env
BOOKNEST_ENV_ID=local
USE_REDIS_IN_LOCAL=False
SEED_LOCAL_ON_FIRST_START=True
```

If you want real Redis locally:

```env
USE_REDIS_IN_LOCAL=True
```

## API Documentation
- Swagger UI: `http://127.0.0.1:8000/api/docs/swagger/`
- ReDoc: `http://127.0.0.1:8000/api/docs/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

## Authentication Endpoints
- Register: `POST /api/users/v1/users/register`
- Verify email OTP: `POST /api/users/v1/users/verify-email`
- Resend verification OTP: `POST /api/users/v1/users/resend-verification`
- Login: `POST /api/users/v1/users/login`
- Profile: `GET /api/users/v1/users/me`
- Token refresh: `POST /api/auth/token/refresh/`
- Token verify: `POST /api/auth/token/verify/`

Header:

```text
Authorization: Bearer <access_token>
```
