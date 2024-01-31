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

A luolaBot container image can be built with nix:

```
nix-build container.nix --argstr imagename "<name-of-your-choice>"
```

The image can then be loaded to Docker and tagged as needed with:

```
docker load < result
docker image tag <name-you-chose-earlier>:<tag-from-the-output-of-previous-command> <name-you-chose-earlier>:<tag-of-your-choice>
```

Additionally there is a k8s manifest to deploy that image as a deployment. For a luolabot container to work, a config file has to be mounted at `/etc/luolabot/luolabot.yaml`. When using k8s, the config should be stored as a secret called `luola-bot-config`. For configuration options, see the "Configuration" section below.

## Configuration

Here is a schema-ish for a luolabot yaml configuration file:

```
token: "<your-bot-token>"
privileged_users:
  - <tg-username->
disable_default_db_api: <boolean>
db_apis:
  - url: "url:port"
    username: "<username>"
    password: "<password>"
    writable: <boolean>

```

Only `token` is mandatory. 

By default, luolabot looks for a configfile called `luolabot.yaml` in the same directory where `luola_bot.py` resides. A custom directory can be set with the `--config` flag when running the bot eg.:

```
python luola_bot.py --config /path/to/config.yaml
```

## Development

LuolaBot can be developped in a nix shell. 

1. Install nix and direnv.
2. Clone this directory.
3. Allow direnv in this directory.


## TODO

1. Add a `/del` command.
2. Make `db_apis.writable` to actually have some effect.
3. Have operator automatically update the config secret and restart the luolabot pod if luolabot CRD is changed.
