import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CHANNEL_EVENTS_TOPIC = os.getenv('CHANNEL_EVENTS_TOPIC')
USER_EVENTS_TOPIC = os.getenv('USER_EVENTS_TOPIC')


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


def challenge_response(challenge):
    logger.info(f'Sending challenge response: {challenge}')
    return response({'challenge': challenge}, 200)


def process_event(data, event_type):
    if event_type == 'channel':
        sns_topic = CHANNEL_EVENTS_TOPIC
    elif event_type == 'user':
        sns_topic = USER_EVENTS_TOPIC
    else:
        return

    sns_client = boto3.client('sns')
    logger.info('Sending Slack event to be processed...')

    try:
        sns_client.publish(
            TopicArn=sns_topic,
            Message=json.dumps(data),
            MessageStructure='string'
        )
    except ClientError as error:
        logger.exception(f'Error sending SNS notification: {error}')


def lambda_handler(event, context):
    body = json.loads(event['body'])
    logger.info(body)

    event_type = body.get('type')
    logger.info(f'Event Type: {event_type}')

    if event_type == 'url_verification':
        return challenge_response(body.get('challenge'))

    if body['event'].get('subtype', '') == 'bot_message':
        logger.info('Ignoring bot messages...')
        return response('OK', 200)

    if event_type == 'event_callback':
        callback_type = body['event'].get('type')
        logger.info(f'Received an event: {event_type}/{callback_type}')

        if callback_type == 'member_joined_channel':
            pass

        elif body['event']['type'] in ('app_mention', 'message'):
            process_event(body, 'user')
            return response('Accepted', 202)

    logger.warning('Unsupported event!')
    return response('Bad Request', 400)
