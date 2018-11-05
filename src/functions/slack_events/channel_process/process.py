import json
import logging
import os
import secrets
import uuid

import boto3
from botocore.exceptions import ClientError
from botocore.vendored import requests
from cryptography.fernet import Fernet

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_parameter(name, decrypt=False):
    ssm_client = boto3.client('ssm')
    resp = ssm_client.get_parameter(Name=name, WithDecryption=decrypt)
    return resp['Parameter']['Value']


CHANNELS_TABLE = os.getenv('CHANNELS_TABLE')
TEAMS_TABLE = os.getenv('TEAMS_TABLE')

dynamodb = boto3.resource('dynamodb')
fernet = Fernet(get_parameter(os.getenv('ENC_KEY_PARAM'), decrypt=True))


class CommandException(Exception):
    pass


def save_channel(team_id, channel_id):
    teams_table = dynamodb.Table(CHANNELS_TABLE)

    endpoint = str(uuid.uuid4())
    username = secrets.token_hex(8)
    password = secrets.token_urlsafe(32)
    try:
        teams_table.update_item(
            Key={
                'team_id': team_id,
                'channel_id': channel_id
            },
            UpdateExpression="set endpoint = :en, "
                             "credentials.username = :cu,"
                             "credentials.password = :cp",
            ExpressionAttributeValues={
                ':en': endpoint,
                ':cu': username,
                ':cp': fernet.encrypt(password.encode())
            },
            ReturnValues="UPDATED_NEW"
        )
    except ClientError:
        logger.exception('Unable to write title entry to DynamoDB!')
        raise


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
