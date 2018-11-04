import json
import logging
import re
import os

import boto3
from botocore.vendored import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_parameter(name, decrypt=False):
    ssm_client = boto3.client('ssm')
    resp = ssm_client.get_parameter(Name=name, WithDecryption=decrypt)
    return resp['Parameter']['Value']


SIGNING_SECRET = get_parameter(os.getenv('SIGNING_SECRET_PARAM'))

I_HAVE_RE = re.compile(r'^i\s+have\s+([\d\s]+)(?<!\s)\s*$')
I_NEED_RE = re.compile(r'^i\s+need\s+([\d\s]+)(?<!\s)\s*$')
I_TRADED_RE = re.compile(
    r'^i\s+traded\s+([\d\s]+)(?<!\s)\s+for\s+([\d\s]+)(?<!\s)\s*$')


class CommandException(Exception):
    pass


def send_chat_message(channel, text, token):
    r = requests.post(
        'https://slack.com/api/chat.postMessage',
        json={
            'channel': channel,
            'text': text,
            'link_names': True
        },
        headers={'Authorization': f'Bearer {token}'},
        timeout=5
    )
    logger.info(f"Slack API response: {r.status_code} {r.json()}")


def lambda_handler(event, context):
    if event.get('Records'):
        logging.info('Processing SNS records...')
        for record in event['Records']:

            data = json.loads(record['Sns']['Message'])
            logger.info(data)

            if data['event']['type'] == 'app_mention':
                input_text = \
                    data['event']['text'].lower().split(maxsplit=1)[-1]

            elif data['event']['type'] == 'message':
                input_text = data['event']['text'].lower()

            else:
                logger.warning(f"Event '{data['event']['type']}' is not supported!")
                continue

            # send_chat_message(
            #     data['event']['channel'],
            #     message_text,
            #     team.bot_access_token
            # )

    else:
        logging.warning('No SNS records found in the event')

    return {}
