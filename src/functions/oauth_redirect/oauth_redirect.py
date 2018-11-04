import logging
import os

import boto3
from botocore.exceptions import ClientError
from botocore.vendored import requests
from cryptography.fernet import Fernet
from opossum import api

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_parameter(name, decrypt=False):
    ssm_client = boto3.client('ssm')
    resp = ssm_client.get_parameter(Name=name, WithDecryption=decrypt)
    return resp['Parameter']['Value']


CLIENT_ID = get_parameter(os.getenv('CLIENT_ID_PARAM'))
CLIENT_SECRET = get_parameter(os.getenv('CLIENT_SECRET_PARAM'), decrypt=True)
DOMAIN_NAME = os.getenv('DOMAIN_NAME')
TEAMS_TABLE = os.getenv('TEAMS_TABLE')

dynamodb = boto3.resource('dynamodb')
fernet = Fernet(get_parameter(os.getenv('ENC_KEY_PARAM'), decrypt=True))


def save_new_team(token_data):
    teams_table = dynamodb.Table(TEAMS_TABLE)

    try:
        teams_table.update_item(
            Key={
                'team_id': token_data['team_id']
            },
            UpdateExpression="set team_name = :tn, "
                             "access_token = :at,"
                             "bot_user_id = :bui,"
                             "bot_access_token = :bat",
            ExpressionAttributeValues={
                ':tn': token_data['team_name'],
                ':at': fernet.encrypt(
                    token_data['access_token'].encode()),
                ':bui': token_data['bot']['bot_user_id'],
                ':bat': fernet.encrypt(
                    token_data['bot']['bot_access_token'].encode())
            },
            ReturnValues="UPDATED_NEW"
        )
    except ClientError:
        logger.exception('Unable to write title entry to DynamoDB!')
        raise


def get_access_tokens(code):
    r = requests.post(
        'https://slack.com/api/oauth.access',
        data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'redirect_uri': f'https://{DOMAIN_NAME}/slack/oauth/redirect'
        },
        timeout=3
    )
    r.raise_for_status()
    return r.json()


@api.handler
def lambda_handler(event, context):
    code = event['queryStringParameters'].get('code')
    error = event['queryStringParameters'].get('error')

    if error:
        print(error)
        return error, 400

    access_tokens = get_access_tokens(code)
    logger.info(f'Access token request response: {access_tokens}')
    if access_tokens['ok']:
        save_new_team(access_tokens)
        return 'success', 200
    else:
        return {'error': access_tokens.get('error')}, 400
