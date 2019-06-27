import requests
import chardet
from random import randint
from time import sleep
import logging

def is_gibberish(content_bytes):
    if chardet.detect(content_bytes)['encoding']:
        return False
    return True
    
def rget(url, session, delay=False):
    if delay:
        sleep(randint(1, 4))
        
    content = session.get(url)
    max_retries = 5
    retries = 0
    while is_gibberish(content.content) and retries <= max_retries:
        logging.info("gibberish encountered. Trying again.")
        sleep(randint(5, 10))
        content = session.get(url)
        retries += 1
        
    if is_gibberish(content.content):
        logging.error("Still gibberish after 5 attempts")
        return None
    else:
        return content