web: flask db upgrade; flask translate compile; gunicorn DNMS:app
worker: venv/bin/celery worker -A DNMS.celery --loglevel=info