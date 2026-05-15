FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ARG APP_ENV=local

COPY requirements /app/requirements
RUN pip install --no-cache-dir -r /app/requirements/${APP_ENV}.txt

COPY . .
RUN chmod +x /app/scripts/*.sh

EXPOSE 8000

CMD ["/bin/sh", "/app/scripts/start.sh"]
