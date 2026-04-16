# Discord Reaction Self-Bot

Simple Discord self-bot that logs in with a user token via `discord.py-self` and reacts to messages from configured users.

## Warning

This uses a Discord user token, not a bot token. That can violate Discord's Terms of Service. Use it only on accounts you control and at your own risk.

Library choice was verified against the official `discord.py-self` package on PyPI and its documentation:

- [discord.py-self on PyPI](https://pypi.org/project/discord.py-self/)
- [discord.py-self FAQ](https://discordpy-self.readthedocs.io/en/latest/faq.html)

## Files

- `main.py`
- `config.py`
- `.env.example`
- `requirements.txt`
- `README.md`

## Features

- Uses `discord.py-self`, not a raw WebSocket client
- Connects with a user token
- Reacts immediately on `on_message`
- Supports 5 reaction slots
- Optional role filtering per slot
- Commands for the authenticated user in any channel:
  - `!able 1`
  - `!disable 1`
  - `!status`
- Persists slot enabled/disabled state to `.env`
- Reconnects automatically through `client.run(..., reconnect=True)`

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configure

Copy the example file:

```bash
copy .env.example .env
```

Set your user token and slots in `.env`.

Example:

```env
DISCORD_USER_TOKEN=your_user_token_here
LOG_LEVEL=INFO

SLOT_ENABLED_1=true
TARGET_USER_ID_1=123456789012345678
ROLE_ID_1=
EMOJI_ID_1=987654321098765432
EMOJI_NAME_1=party
```

## Slot rules

- `SLOT_ENABLED_X`: whether slot `X` is active
- `TARGET_USER_ID_X`: the user to watch
- `ROLE_ID_X`: optional guild role filter
- `EMOJI_ID_X`: custom emoji ID
- `EMOJI_NAME_X`: custom emoji name or Unicode emoji

Emoji behavior:

- Custom emoji:
  - set `EMOJI_ID_X`
  - set `EMOJI_NAME_X` as well for best compatibility
- Unicode emoji:
  - leave `EMOJI_ID_X` empty
  - put the emoji directly in `EMOJI_NAME_X`

## Commands

These only work when sent by the authenticated user account:

- `!able <n>` enables a slot
- `!disable <n>` disables a slot
- `!status` sends an embed with all slot states

Example:

```text
!able 1
!disable 2
!status
```

## Run

```bash
python main.py
```

## Notes

- Role filtering only applies in guilds.
- If you configure your own user ID in a slot, the client can react to your own non-command messages.
- If a custom emoji ID is set but the emoji is not in cache, the code falls back to the `<:name:id>` format when `EMOJI_NAME_X` is provided.