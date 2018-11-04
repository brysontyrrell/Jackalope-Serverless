import os

import boto3


def get_parameter(name, decrypt=False):
    ssm_client = boto3.client('ssm')
    resp = ssm_client.get_parameter(Name=name, WithDecryption=decrypt)
    return resp['Parameter']['Value']


CLIENT_ID = get_parameter(os.getenv('CLIENT_ID_PARAM'))
DOMAIN_NAME = os.getenv('DOMAIN_NAME')


def lambda_handler(event, context):
    redirect_url = f'https://slack.com/oauth/authorize?client_id={CLIENT_ID}&' \
                   f'scope=bot,chat:write:bot&' \
                   f'redirect_uri=https://{DOMAIN_NAME}/slack/oauth/redirect'

    return {
        'isBase64Encoded': False,
        'statusCode': 302,
        'body': '',
        'headers': {'Location': redirect_url}
    }
