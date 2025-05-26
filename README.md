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

Additionally there is a k8s manifest to deploy that image as a deployment. For a luolabot container to work, a config file has to be mounted at `/etc/luolabot/luolabot.yaml`. 

### K8s operator way

To deploy a luolaBot container on k8s, one can use luolabot's k8s operator. For that, one should deployt the manifests in the `manifests` firecotry to k8s. Then one needs to deploy a custom resource of kind `luolabot`. A schema-ish for the custom resource can be found under 'Configuration: k8s custom luolabot resource'.

#### Author's own deployment

I deploy the bot using ArgoCD with a custom CouchDB on k8s. To setup the bot, I do the following:

```
argocd app create luolabot --repo https://github.com/juuso22/luolaBot.git --path manifests --dest-server <server>
helm repo add couchdb https://apache.github.io/couchdb-helm
helm repo update
helm install luola-couch couchdb/couchdb   --version=4.5.0   --set couchdbConfig.couchdb.uuid=$(curl https://www.uuidgenerator.net/api/version4 2>/dev/null | tr -d -)
#The next 3 command require files that you need to create: the kubeconfig you need to figure out depending on your k8s installation. I have added hints for the other 2
kubectl create secret generic --from-file kubeconf.yaml luola-bot-kube-config
kubectl create secret generic --from-file token luola-bot-token #Look at 'Configuration: k8s custom luolabot resource' in this README to figure out the content of the token file.
kubectl create secret generic --from-file password luola-couch-pw #The helm install command helps to find content to create the password file
```

## Configuration

Here is a schema-ish for a luolabot yaml configuration file:

```
token: "<your-bot-token>"
privileged_users:
  - <tg-username>
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

### k8s custom luolabot resource

Here is a schema-ish for a luolabot k8s custom resource:

```
apiVersion: luolabot.tg/v1
kind: LuolaBot
metadata:
  name: <name-of-your-choosing>
spec:
  botTokenSecret: <secret-containing-the-bot token>
  image: <luolabot-container-image-eg: ghcr.io/juuso22/luolabot:0.0.5>
  privileged_users:
  - <list-of-users>
 db_apis:
  - url: "<url>:<port>"
    username: "<username>"
    passwordSecret: "<secret-containing-the-db-password>"
    writable: true
```

The token secret needs to be of form `token: <token-value>`.

For custom database password secrets need to be of form `password: <password>`.

## Development

LuolaBot can be developped in a nix shell. 

1. Install nix and direnv.
2. Clone this directory.
3. Allow direnv in this directory.


## TODO

* Make operator deploy CouchDb, if needed
* Try to figure out is there a 'canonical' way to pass the kubeconfig to the operator
