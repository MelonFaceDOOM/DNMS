FROM nickgryg/alpine-pandas

#create login with no password
RUN adduser -D dnms

WORKDIR /home/dnms

COPY requirements.txt requirements.txt

# for pyscopg2 (for postgresql)
# RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

# for pyzmqt
RUN apk add build-base libzmq python3 zeromq-dev

# for lxml
RUN apk add g++ libxslt-dev
# RUN apk add libxml2-dev libxslt1-dev

RUN python -m venv venv
RUN pip install --upgrade pip
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql

COPY app app
COPY migrations migrations
COPY DNMS.py extensions.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP DNMS.py

RUN chown -R dnms:dnms ./
USER dnms

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
