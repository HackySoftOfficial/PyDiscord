# WebSocket API Documentation

## Overview

This documentation covers the WebSocket API for a FastAPI application. The WebSocket allows real-time communication for various operations including user registration, login, and data manipulation related to users, channels, and guilds.

## NOTICE
In every command must be passed `Bearer {token}` except in login and register commands

## WebSocket Endpoint

### URL
```
/ws
```

### Method
```
WebSocket
```

### Description
Establishes a WebSocket connection and processes commands for user authentication and various operations.

## Usage

1. **Connect to the WebSocket Server**
   - Use a WebSocket client to connect to the `/ws` endpoint.
   - Send a JSON payload with a command and payload data as needed.

2. **Commands and Payloads**

### Command: `register`

**Payload:**
```json
{
  "command": "register",
  "payload": {
    "username": "example_user",
    "email": "user@example.com",
    "password": "secure_password"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "user": {
    "id": 1,
    "username": "example_user",
    "email": "user@example.com",
    "display_name": null,
    "avatar_url": null,
    "about_me": null,
    "pronouns": null
  }
}
```

### Command: `login`

**Payload:**
```json
{
  "command": "login",
  "payload": {
    "username": "example_user",
    "password": "secure_password"
  }
}
```

**Response:**
```json
{
  "access_token": "your_access_token_here",
  "token_type": "bearer"
}
```

### Command: `get_user`

**Payload:**
```json
{
  "command": "get_user",
  "payload": {
    "user_id": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "user": {
    "id": 1,
    "username": "example_user",
    "email": "user@example.com",
    "display_name": "Example User",
    "avatar_url": "http://example.com/avatar.jpg",
    "about_me": "About me",
    "pronouns": "he/him"
  }
}
```

### Command: `update_user`

**Payload:**
```json
{
  "command": "update_user",
  "payload": {
    "display_name": "New Display Name",
    "avatar_url": "http://example.com/new_avatar.jpg"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "user": {
    "id": 1,
    "username": "example_user",
    "email": "user@example.com",
    "display_name": "New Display Name",
    "avatar_url": "http://example.com/new_avatar.jpg",
    "about_me": "About me",
    "pronouns": "he/him"
  }
}
```

### Command: `create_guild`

**Payload:**
```json
{
  "command": "create_guild",
  "payload": {
    "name": "New Guild"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "guild": {
    "id": 1,
    "name": "New Guild",
    "owner_id": 1
  }
}
```

### Command: `get_guild`

**Payload:**
```json
{
  "command": "get_guild",
  "payload": {
    "guild_id": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "guild": {
    "id": 1,
    "name": "New Guild",
    "owner_id": 1
  }
}
```

### Command: `delete_guild`

**Payload:**
```json
{
  "command": "delete_guild",
  "payload": {
    "guild_id": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Guild deleted"
}
```

### Command: `create_channel`

**Payload:**
```json
{
  "command": "create_channel",
  "payload": {
    "name": "New Channel",
    "guild_id": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "channel": {
    "id": 1,
    "name": "New Channel",
    "guild_id": 1
  }
}
```

### Command: `get_channel`

**Payload:**
```json
{
  "command": "get_channel",
  "payload": {
    "channel_id": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "channel": {
    "id": 1,
    "name": "New Channel",
    "guild_id": 1
  }
}
```

### Command: `update_channel`

**Payload:**
```json
{
  "command": "update_channel",
  "payload": {
    "channel_id": 1,
    "channel_update": {
      "name": "Updated Channel Name"
    }
  }
}
```

**Response:**
```json
{
  "status": "success",
  "channel": {
    "id": 1,
    "name": "Updated Channel Name",
    "guild_id": 1
  }
}
```

### Command: `delete_channel`

**Payload:**
```json
{
  "command": "delete_channel",
  "payload": {
    "channel_id": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Channel deleted"
}
```

### Command: `request_invite`

**Payload:**
```json
{
  "command": "request_invite",
  "payload": {
    "guild_id": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "invite_code": "generated_invite_code_here"
}
```

### Command: `join_guild`

**Payload:**
```json
{
  "command": "join_guild",
  "payload": {
    "invite_code": "generated_invite_code_here"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Joined guild"
}
```

### Command: `list_user_guilds`

**Payload:**
```json
{
  "command": "list_user_guilds",
  "payload": {}
}
```

**Response:**
```json
{
  "status": "success",
  "guilds": [
    {
      "id": 1,
      "name": "New Guild",
      "owner_id": 1
    }
  ]
}
```

### Command: `set_status`

**Payload:**
```json
{
  "command": "set_status",
  "payload": {
    "status": "online"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "status": "online"
}
```

### Command: `get_user_status`

**Payload:**
```json
{
  "command": "get_user_status",
  "payload": {
    "user_id": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "user_id": 1,
  "status": "online"
}
```

### Command: `get_channel_users`

**Payload:**
```json
{
  "command": "get_channel_users",
  "payload": {
    "channel_id": 1,
    "page": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "page": 1,
  "total_pages": 1,
  "users": [
    {
      "id": 1,
      "username": "example_user",
      "email": "user@example.com",
      "display_name": "Example User",
      "avatar_url": "http://example.com/avatar.jpg",
      "about_me": "About me",
      "pronouns": "he/him"
    }
  ]
}
```

### Command: `get_messages`

**Payload:**
```json
{
  "command": "get_messages",
  "payload": {
    "channel_id": 1,
    "page": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "page": 1,
  "total_pages": 1,
  "messages": [
    {
      "id": 1,
      "content": "Hello World!"
    }
  ]
}
```

### Command: `send_message`

**Payload:**
```json
{
  "command": "send_message",
  "payload": {
    "channel_id": 1,
    "content": "New message content"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message_id": 1,
  "content": "New message content"
}
```

### Command: `get_guild_channels`

**Payload:**
```json
{
  "command": "get_guild_channels",
  "payload": {
    "guild_id": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "channels": [
    {
      "id": 1,
      "name": "general",
      "guild_id": 1
    },
    {
      "id": 2,
      "name": "random",
      "guild_id": 1
    },
    {
      "id": 3,
      "name": "announcements",
      "guild_id": 1
    }
  ]
}
```

### Command: `create_channel`

**Payload:**
```json
{
  "command": "create_channel",
  "payload": {
    "guild_id": 1,
    "name": "new-channel-name"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "channel": {
    "id": 1,
    "name": "new-channel-name",
    "guild_id": 1
  }
}
```

### Command: `delete_channel`

**Payload:**
```json
{
  "command": "delete_channel",
  "payload": {
    "channel_id": 1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "detail": "Channel new-channel-name deleted successfully"
}
```
