# Environment setup

make here 3 files with the following content where envreadme.md is:

1. .env.development
2. .env.staging
3. .env.production


# Django settings
DJANGO_ENVIRONMENT=development
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
DATABASE_URL=postgresql://postgres:new_password@localhost:5432/test

# Uncomment if your Django project uses these direct settings instead of DATABASE_URL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=test
DB_USER=postgres
DB_PASSWORD=new_password
DB_HOST=localhost
DB_PORT=5432

# These are likely for Docker/container setup and may not affect Django directly
POSTGRES_DB=test
POSTGRES_USER=postgres
POSTGRES_PASSWORD=new_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Celery settings 
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=django-db
CELERY_TASK_ALWAYS_EAGER=False
CELERY_TASK_TRACK_STARTED=True
CELERY_TASK_TIME_LIMIT=30
CELERY_WORKER_SEND_TASK_EVENTS=True
CELERY_TASK_SEND_SENT_EVENT=True