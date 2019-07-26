web: flask db upgrade; flask translate compile; gunicorn DNMS:app
worker: celery worker -A DNMS.celery --loglevel=info