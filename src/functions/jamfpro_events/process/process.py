import json
import logging
import re
import os

from botocore.vendored import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

I_HAVE_RE = re.compile(r'^i\s+have\s+([\d\s]+)(?<!\s)\s*$')
I_NEED_RE = re.compile(r'^i\s+need\s+([\d\s]+)(?<!\s)\s*$')
I_TRADED_RE = re.compile(
    r'^i\s+traded\s+([\d\s]+)(?<!\s)\s+for\s+([\d\s]+)(?<!\s)\s*$')


def lambda_handler(event, context):
    if event.get('Records'):
        logging.info('Processing SNS records...')
        for record in event['Records']:
            data = json.loads(record['Sns']['Message'])
            logger.info(data)
    else:
        logging.warning('No SNS records found in the event')

    return {}
