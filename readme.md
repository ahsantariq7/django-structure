mkdir -p my_project/{management,microservices}
cd my_project

#create venv
python3 -m venv venv

#activate venv
source venv/bin/activate

1- pip install poetry


# For Django Management
cd management
poetry init --no-interaction \
  --name "management" \
  --description "Django management application for database and admin operations" \
  --author "Your Name <your.email@example.com>" \
  --python ">=3.11,<4.0"
  
# Copy the pyproject.toml content above and replace the file

# For FastAPI Microservices
cd ../microservices
poetry init --no-interaction \
  --name "microservices" \
  --description "FastAPI microservices for API operations" \
  --author "Your Name <your.email@example.com>" \
  --python ">=3.11,<4.0"
  
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


python manage.py createapp myapp
python removeapp.py myapp

python manage.py renameapp myapp newapp
# Basic usage - finds and fixes all migration issues
python manage.py fixmigrations

# Preview what would be fixed without making changes
python manage.py fixmigrations --dry-run

# Also fix stale content types
python manage.py fixmigrations --fix-contenttypes

# Use fake-initial when applying missing migrations
python manage.py fixmigrations --fake-initial

# Skip confirmation prompt
python manage.py fixmigrations --force

python manage.py clear_database