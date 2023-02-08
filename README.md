# luolaBot

Telegram bot spitting out DnD 5e rules. Written in Python.

## Running/deploying the bot

### The easy way

Install prerequisite packages with pip:

```
pip install requests
pip install aiohttp
pip install python-telegram-bot
pip install pyyaml
pip install habot
```

Get a Telegram bot token from botFather.

Then clone this bot repo and create a file called `luolabot.yaml` which contains the following:

```
token: "<your-bot-token>"
```

and then run:

```
python luola_bot.py
```

### Container way

The repo contains a `Dockerfile` to build a nixos-based container image for luolabot. Additionally there is a k8s manifest to deploy that image as a stateful set and a manifest for the service needed with stateful sets. For a luolabot container to work a config file has to be mounted at `/etc/luolabot/luolabot.yaml`. When using k8s, the config should be stored as a secret called `luola-bot-config`. For configuration options, see the "Configuration" section below.

## Configuration

Here is a schema for a luolabot yaml configuration file:

```
instances:
  - <optional-list-of-instance-hostnames-or-ips-if-you-desire-to-run-"ha"-bot>
  - <another-instance-hostname-or-ip>
token: "<your-bot-token>"

```

By default, luolabot looks for a configfile called `luolabot.yaml` in the same directory where `luola_bot.py` resides. A custom directory can be set with the `--config` flag when running the bot eg.:

```
python luola_bot.py --config /path/to/config.yaml
```

## Development

LuolaBot can be developped in a nix shell. 

1. Install nix and direnv.
2. Clone this directory.
3. Allow direnv in this directory.
4. `luolabot` as a "binary" with all its dependencies should be available for you inside a nix shell.
