# Dark Net Market Scraping

1) clone repository
2) python3 -m venv venv
3) source venv/bin/activate
4) pip install -r requirements.txt
5) flask run
6) ./run-redis.sh
7) venv/bin/celery worker -A DNMS.celery --loglevel=info
