import hashlib
import hmac
import json
import logging
import os
import time

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_parameter(name, decrypt=False):
    ssm_client = boto3.client('ssm')
    resp = ssm_client.get_parameter(Name=name, WithDecryption=decrypt)
    return resp['Parameter']['Value']


SIGNING_SECRET = get_parameter(os.getenv('SIGNING_SECRET_PARAM'), decrypt=True)
CHANNEL_EVENTS_TOPIC = os.getenv('CHANNEL_EVENTS_TOPIC')
USER_EVENTS_TOPIC = os.getenv('USER_EVENTS_TOPIC')


def validate_request(event):
    request_body = event['body']
    request_timestamp = event['headers']['X-Slack-Request-Timestamp']
    request_signature = event['headers']['X-Slack-Signature']

    if (int(time.time()) - int(request_timestamp)) > (60 * 5):
        logger.error('Request timestamp if older than 5 minutes!')
        return False

    base_string = f'v0:{request_timestamp}:{request_body}'

    generated_sig = 'v0=' + hmac.HMAC(
        bytes(SIGNING_SECRET, 'utf-8'),
        bytes(base_string, 'utf-8'),
        hashlib.sha256
    ).hexdigest()

    logger.info(f'Request Signature:   {request_signature}\n'
                f'Generated Signature: {generated_sig}')
    return hmac.compare_digest(request_signature, generated_sig)


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
    logger.info(event)
    if not validate_request(event):
        logger.error('Signature verification on incoming request failed!')
        return response('Forbidden', 403)

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
            process_event(body, 'channel')
            return response('Accepted', 202)

        elif body['event']['type'] in ('app_mention', 'message'):
            process_event(body, 'user')
            return response('Accepted', 202)

    logger.warning('Unsupported event!')
    return response('Bad Request', 400)
