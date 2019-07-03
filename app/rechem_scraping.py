import requests
import chardet
from random import randint
from time import sleep
import logging

def is_gibberish(content_bytes):
    if chardet.detect(content_bytes)['encoding']:
        return False
    return True
    
def rget(url, session):
    content = session.get(url)
    max_retries = 5
    retries = 0

    while True:
        if is_gibberish(content.content):
            if retries >= max_retries - 1:
                logging.info("Giving up after encountering gibberish after {} retries at {}".format(retries, url))
                return None
            logging.info("gibberish encountered after {} retries at {}".format(retries, url))
            sleep(randint(5, 10))
            content = session.get(url)
            retries += 1
        else:
            logging.info("Success after {} retries at {}".format(retries, url))
            return content