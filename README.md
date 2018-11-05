# Jackalope

A Slack bot and notification service for Jamf Pro administrators.

## Database

### Teams Table

- team_id (key)
- team_name
- access_token
- bot_user_id
- bot_access_token

### Channels Tables

- team_id (key)
- channel_id (key)
- endpoint
- credentials
    - username
    - password
