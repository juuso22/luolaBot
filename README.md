# luolaBot

Telegram bot spitting out DnD 5e rules. Written in Python.

## Using the bot

You can get rules with:

```
/<rule-category> <rule>
```

`<rule-category>` can be eg. spell, condition, feature or class. Special `<rule-category>` class-level allows to sort class features by level. `<rule>` could be eg. the spell Hunter\'s Mark or the feature rage.

You can roll dice with one of the following:

```
/roll xdy + z
/rxdypz
```

Rules given by this bot come by default from http://www.dnd5eapi.co/

### Additional databases

There is a possibility to define additional databases. See the section about 'Configuration' below on what is needed. At the current amvp (almost a minimal viable product) stage, only the second database of the eventual list of databases is editable. The edits are only allowed for a set of specified users, so you want to run your own instance of luolaBot to have that functionality (see the section 'Running/deploying the bot' below in addition to the section 'Configuration'). Currently, I have only tried CouchDB as an additional database and the code has some quirks that are unlikely to work with something else for the time being.

For an editable database, you can use the following additional commands to add and delete rules to/from this db:

*Adding a rule:*

```
/add <category-of-the-new-thing-to-add-eg-equipment-or-monsters> <data-in-json>
```

The `<data-in-json>` needs to have at least name as attribute. There might be additional fields needed when displaying the newly added content. I will try to handle these in the future.

Example (note the plural in the category `monsters`): 

```
/add monsters {"name": "Peijooni", "actions": [{"name": "Claw attack", "desc": "1d6 + 2 piercing damage"}]
```

*Deleting a rule*

```
/rm <category-of-the-new-thing-to-add-eg-equipment-or-monsters> <name-or-index-of-the-object-to-be-deleted>
```

Index is same as the name in lower case with some special characters removed and spaces replaced with dashes (-).

Example:

```
/rm monsters peijooni
```

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

