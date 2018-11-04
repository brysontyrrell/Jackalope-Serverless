import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

EVENTS_TOPIC = os.getenv('EVENTS_TOPIC')


def response(message, status_code):
    """Returns a dictionary object for an API Gateway Lambda integration
    response.

    :param message: Message for JSON body of response
    :type message: str or dict

    :param int status_code: HTTP status code of response

    :rtype: dict
    """
    if isinstance(message, str):
        message = {'message': message}

    return {
        'isBase64Encoded': False,
        'statusCode': status_code,
        'body': json.dumps(message),
        'headers': {'Content-Type': 'application/json'}
    }


# def process_event(data):
#     sns_client = boto3.client('sns')
#     logger.info('Sending Slack event to be processed...')
#
#     try:
#         sns_client.publish(
#             TopicArn=EVENTS_TOPIC,
#             Message=json.dumps(data),
#             MessageStructure='string'
#         )
#     except ClientError as error:
#         logger.exception(f'Error sending SNS notification: {error}')


def lambda_handler(event, context):
    # body = json.loads(event['body'])
    # logger.info(body)
    logger.info(event)
    return response('Success', 200)
    # logger.warning('Bad Request')
    # return response('Bad Request', 400)
