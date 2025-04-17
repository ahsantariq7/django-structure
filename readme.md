# Django/FastAPI Project

  
# Copy the pyproject.toml content above and replace the file

#for management pyproject.toml

```
[tool.poetry]
[tool.poetry]
name = "management"
version = "0.1.0"
description = "Django management application for database and admin operations"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
package-mode = false

[tool.poetry.dependencies]
python = "^3.11"
django = "^4.2.7"
djangorestframework = "^3.14.0"
django-cors-headers = "^4.3.0"
psycopg2-binary = "^2.9.9"
celery = "^5.3.4"
django-celery-results = "^2.5.1"
django-celery-beat = "^2.5.0"
redis = "^5.0.1"
gunicorn = "^21.2.0"
python-dotenv = "^1.0.0"
pydantic = "^2.4.2"
pydantic-settings = "^2.0.3"

[tool.poetry.group.dev.dependencies]
black = "^23.10.1"
isort = "^5.12.0"
flake8 = "^6.1.0"
pytest = "^7.4.3"
pytest-django = "^4.5.2"
pytest-cov = "^4.1.0"
mypy = "^1.6.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ["py311"]
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.development"
python_files = "test_*.py"
testpaths = ["tests"]
```

#for microservices pyproject.toml

```
[tool.poetry]
name = "microservices"
version = "0.1.0"
description = "FastAPI microservices for API operations"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
package-mode = false

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.23.2"}
sqlalchemy = "^2.0.23"
alembic = "^1.12.1"
pydantic = "^2.4.2"
pydantic-settings = "^2.0.3"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.6"
psycopg2-binary = "^2.9.9"
redis = "^5.0.1"
httpx = "^0.25.1"
tenacity = "^8.2.3"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
black = "^23.10.1"
isort = "^5.12.0"
flake8 = "^6.1.0"
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
mypy = "^1.6.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ["py311"]
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

# Environment Setup

This document explains how to set up the environment configuration for different deployment stages of your Django project.

## Creating Environment Files

Create the following three environment files in the project root directory:

1. `.env.development` - For local development environments
2. `.env.staging` - For staging/testing environments
3. `.env.production` - For production environments

## Environment File Templates

Each environment file should contain the configuration variables listed below, with values adjusted according to the specific environment.

### Development Environment (`.env.development`)

# Django settings
DJANGO_ENVIRONMENT=development
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
DATABASE_URL=postgresql://postgres:new_password@localhost:5432/test

# Direct database settings
DB_ENGINE=django.db.backends.postgresql
DB_NAME=test
DB_USER=postgres
DB_PASSWORD=new_password
DB_HOST=localhost
DB_PORT=5432

# PostgreSQL container settings
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
```

### Staging Environment (`.env.staging`)

Use the same template as development but with these changes:

```
DJANGO_ENVIRONMENT=staging
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=staging-secret-key-should-be-different
DJANGO_ALLOWED_HOSTS=staging.example.com,staging-api.example.com
```

### Production Environment (`.env.production`)

Use the same template as development but with these changes:

```
DJANGO_ENVIRONMENT=production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=secure-production-secret-key
DJANGO_ALLOWED_HOSTS=example.com,www.example.com,api.example.com
```

## Configuration Variables Explained

| Variable | Description |
|----------|-------------|
| `DJANGO_ENVIRONMENT` | Environment identifier (`development`, `staging`, or `production`) |
| `DJANGO_DEBUG` | Debug mode flag (set to `False` in production) |
| `DJANGO_SECRET_KEY` | Django's secret key (unique per environment and kept secret) |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated list of allowed hosts |
| `DATABASE_URL` | Database connection string |
| `DB_*` | Direct database connection parameters |
| `POSTGRES_*` | PostgreSQL container configuration |
| `CELERY_*` | Celery task queue configuration settings |

## Loading Environment Variables

The project is configured to automatically load the appropriate environment file based on the `DJANGO_ENVIRONMENT` setting. Make sure your settings configuration includes logic to load these environment variables.

## Security Considerations

- Never commit `.env.*` files to version control
- Use strong, unique secret keys for each environment
- Restrict `ALLOWED_HOSTS` to necessary domains only
- Use different database credentials for each environment

# Django/FastAPI Project

A modern web application with Django for management and FastAPI for microservices.

## Project Structure

```
my_project/
├── management/             # Django management application
│   ├── apps/               # Django applications
│   │   ├── config/         # Project configuration
│   │   │   ├── management/ # Custom management commands
│   │   │   ├── settings/   # Environment-specific settings
│   │   │   └── urls.py     # URL configuration
│   │   └── ...            # Other Django apps
│   ├── .env.development    # Development environment variables
│   ├── .env.staging        # Staging environment variables
│   ├── .env.production     # Production environment variables
│   ├── manage.py           # Django management script
│   └── pyproject.toml      # Poetry dependencies for Django
├── microservices/          # FastAPI microservices
│   ├── app/                # FastAPI application
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core functionality
│   │   ├── db/             # Database models and connection
│   │   └── main.py         # FastAPI application entry point
│   ├── alembic/            # Database migrations
│   ├── .env                # Environment variables
│   └── pyproject.toml      # Poetry dependencies for FastAPI
└── venv/                   # Python virtual environment
```

## Development Setup

### Initial Setup

```bash
mkdir -p my_project/{management,microservices}
cd my_project

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Poetry
pip install poetry
```

### Django Management Setup

```bash
cd management
poetry init --no-interaction \
  --name "management" \
  --description "Django management application for database and admin operations" \
  --author "Your Name <your.email@example.com>" \
  --python ">=3.11,<4.0"

# Install dependencies
poetry install

# Create environment files
cp envreadme.md .env.development
# Edit .env.development with your configuration

# Initialize Django project
django-admin startproject config .

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### FastAPI Microservices Setup

```bash
cd ../microservices
poetry init --no-interaction \
  --name "microservices" \
  --description "FastAPI microservices for API operations" \
  --author "Your Name <your.email@example.com>" \
  --python ">=3.11,<4.0"

# Install dependencies
poetry install

# Create environment file
touch .env
# Edit .env with your configuration

# Run development server
uvicorn app.main:app --reload
```

## Custom Management Commands

### App Management

```bash
# Create a new Django app
python manage.py createapp myapp

# Remove an existing app
python manage.py removeapp myapp

# Rename an app
python manage.py renameapp myapp newapp
```

### Database Management

```bash
# Fix migration issues
python manage.py fixmigrations

# Preview migration fixes without making changes
python manage.py fixmigrations --dry-run

# Fix stale content types
python manage.py fixmigrations --fix-contenttypes

# Apply missing migrations with --fake-initial
python manage.py fixmigrations --fake-initial

# Skip confirmation prompt
python manage.py fixmigrations --force

# Clear database
python manage.py clear_database
```

## Deployment

### Django Management Application

1. Set up production environment:
   ```bash
   cp .env.development .env.production
   # Edit .env.production with production settings
   ```

2. Collect static files:
   ```bash
   python manage.py collectstatic
   ```

3. Run with Gunicorn:
   ```bash
   gunicorn config.wsgi:application
   ```

### FastAPI Microservices

1. Build the application:
   ```bash
   cd microservices
   ```

2. Run with Uvicorn:
   ```bash
   uvicorn app.main:app --workers 4
   ```

## Docker Support

For containerized deployment, you can create Docker configurations:

```bash
# Build Django management container
docker build -t management -f management/Dockerfile .

# Build FastAPI microservices container
docker build -t microservices -f microservices/Dockerfile .

# Run with Docker Compose
docker-compose up -d
```

## Testing

### Django Tests

```bash
cd management
pytest
```

### FastAPI Tests

```bash
cd microservices
pytest
```

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request