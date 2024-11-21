# Wipe Countdown Bot

Discord bot for managing Rust server wipe schedules and publishing live countdown embeds.

## Overview

Wipe Countdown Bot allows staff to create and manage server wipe schedules directly from Discord. It supports recurring schedules, weekly force wipes, custom wipe patterns and live BattleMetrics player counts.

The project was originally developed as a commercial Rust server tool and has been prepared here as a public portfolio project.

## Features

- Supports Monthly, Weekly, Biweekly and Custom wipe schedules.
- Automatically accounts for the weekly force wipe.
- Refreshes BattleMetrics player counts in embed messages.
- Provides commands for creating, editing, listing and deleting servers and embeds.
- Stores schedules and embed settings in MongoDB.
- Includes Docker deployment with non-root execution and automatic restarts.

## Technology

- Python
- Discord.py
- MongoDB with Motor
- BattleMetrics API
- Docker and Docker Compose

## Configuration

Copy `.env.example` to `.env` and provide the required values:

| Variable | Description |
| --- | --- |
| `DISCORD_BOT_TOKEN` | Discord bot token. |
| `MONGO_URL` | MongoDB connection string. |
| `GUILD_ID` | Discord server ID. |
| `STAFF_ROLE_ID` | Role ID permitted to manage schedules. |
| `BOT_PREFIX` | Command prefix, defaulting to `!`. |
| `SERVER_NAME` | Name displayed in embeds. |
| `EMBED_HEX_COLOR` | Embed colour, such as `#5865F2`. |
| `MONGO_DATABASE` | Database name, defaulting to `rust_wipes`. |

Secrets are loaded from environment variables and are never stored in JSON or committed to Git.

## Running with Docker

```bash
cp .env.example .env
# Fill in .env
docker compose up -d --build
```

View logs with:

```bash
docker compose logs -f
```

The Discord Message Content intent must be enabled in the Discord Developer Portal.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Run the tests with:

```bash
python -m unittest discover -s tests -v
```

## Project status

The scheduling, configuration and deployment paths have been tidied up for public presentation. Further production work would include Discord/MongoDB integration tests, database migrations and a CI pipeline.
