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

Then clone this bot repo and create a file called `luolabot.yaml` which contains the following:

```
token: "<your-bot-token>"
```

and then run:

```
python luola_bot.py
```

### The fancy way

LuolaBot can also be deployed using to a k8s cluster using ansible. You need to have ansible installed. Also, make sure, you have a kubernetes cluster available and you you can ssh to a node on that cluster from which you can apply manifests to that cluster. Finally, you need to have root access with your ssh user to that node (I might change (fix?) this in the future).

NB1: The following ansible playbook will install kubernetes python library on your target node.

NB2: The luolaBot deployment pods are allowed on master node, because I'm lazy and run a single-node k8s cluster myself.

1. Clone this repo.
1. Inside the repo create a file called `hosts` which contains _only_ your chosen target node's ip/hostname.
1. From inside this directory, run:
```
$ ansible-playbook -i hosts -u <your-ssh-user-on-the-target-node> --private-key <private-key-for-the-ssh-user> luola-bot-playbook.yaml
```
1. Give your bot token, when ansible prompts for it.
1. Profit.
