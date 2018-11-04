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


def process_command(input_text):
    message_text = ''

    try:
        if input_text.startswith('help'):
            message_text = \
                "Jamf the Gathering helps you find other JNUC attendees on " \
                "Slack who have cards to trade with you in your quest to " \
                "complete the full set of 18!\n\nJust send me the " \
                "following commands to say which cards you have and which " \
                "cards you need:\n\n```\nI have 1 2 3\nI need 4 5 6```\nAs " \
                "you make trades, you can report them and update your " \
                "available cards using:\n```I traded 1 2 for 4 5```\n" \
                "To find other users to trade with, type:```Show trades```\n" \
                "To see what cards you have flagged as have or need, type:\n" \
                "```show mine```"

    except CommandException:
        message_text = 'Whoops, something went wrong!'

    if not message_text:
        message_text = "I'm sorry, I'm not sure what you wanted me to do? " \
                       "Type 'Help' to learn how I work!"

    return message_text


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

            message_text = process_command(input_text)

            if not message_text:
                logger.info('Unknown command or request')
                continue

            # send_chat_message(
            #     data['event']['channel'],
            #     message_text,
            #     team.bot_access_token
            # )

    else:
        logging.warning('No SNS records found in the event')

    return {}
