# BookNest – Hotel Booking API

Django REST API for a Booking.com-like service: users, hotels, rooms, bookings (JWT auth, permissions, filtering, Swagger docs).

## Tech Stack
- Python 3.x
- Django
- Django REST Framework
- JWT (djangorestframework-simplejwt)
- drf-spectacular (OpenAPI/Swagger)
- django-filter
- Redis (cache, temporary data, rate limiting)

## Setup

### 1) Create virtualenv and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # mac/linux
# venv\Scripts\activate   # windows

pip install -r requirements.txt
```

### 2) Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3) Create admin user (optional)
```bash
python manage.py createsuperuser
```

### 4) Run server
```bash
python manage.py runserver
```

## Docker

Set `BOOKNEST_ENV_ID` in `.env` and the single `compose.yml` will switch
behavior automatically.

### Local setup (SQLite)
```bash
# in .env
BOOKNEST_ENV_ID=local

docker compose up --build
```

### Production-like setup (PostgreSQL)
```bash
# in .env
BOOKNEST_ENV_ID=prod

docker compose up --build
```


### Redis settings
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_TTL_SECONDS=300
TEMP_DATA_TTL_SECONDS=300
LANGUAGE_PREFERENCE_TTL_SECONDS=2592000
RATE_LIMIT_ANON=100/hour
RATE_LIMIT_USER=1000/hour
RATE_LIMIT_AUTH=10/minute
```


## API Documentation (Swagger)
- Swagger UI: http://127.0.0.1:8000/api/docs/
- OpenAPI schema: http://127.0.0.1:8000/api/schema/

## Authentication (JWT)
- Register: `POST /api/auth/register/`
- Login: `POST /api/auth/login/`
- Refresh: `POST /api/auth/refresh/`
- Profile: `GET /api/me/`

Header:
```
Authorization: Bearer <access_token>
```
