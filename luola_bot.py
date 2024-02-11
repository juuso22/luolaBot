#!/root/.nix-profile/bin/python3
import argparse
import asyncio
import aiohttp
import json
import logging
from os.path import exists
import random
import re
import requests as req
import socketserver
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import yaml

DND_API_URL = "https://www.dnd5eapi.co/api"
db_apis = [DND_API_URL]
allowed_users = []
writable_api = None
socketserver.TCPServer.allow_reuse_address = True

# function to handle the /start command
async def start(update, context):
    await update.message.reply_text('Dime do dungeon!')

# function to handle the /help command
async def help(update, context):
    await update.message.reply_text('''Lousy bot that spits out DnD 5e rules:
Usage:
/<rule-category> <rule>
<rule-category> can be eg. spell, condition, feature or class.
Special <rule-category> class-level allows to sort class features by level.
<rule> could be eg. the spell Hunter\'s Mark or the feature rage.
/roll xdy + z
/rxdypz
Rules given by this bot come by default from http://www.dnd5eapi.co/
Additional rule dbs can be defined and interacted with. See the README in the GitHub repo for details.
Bot code can be found in: https://github.com/juuso22/luolaBot''')

def only_allowed_users(func):
    async def check_allowed_users(*args, **kwargs):
        user = args[0].message.from_user.username
        if user in allowed_users:            
            await func(*args, **kwargs)
        else:
            await args[0].message.reply_text(f'User {user} not in allowed users.')
    return check_allowed_users

def only_if_writable_api_exists(func):
    async def execute_command_if_writable_api_exists(*args, **kwargs):
        if writable_api != None:
            await func(*args, **kwargs)
        else:
            await args[0].message.reply_text(f'There is no writable DB :(')
    return execute_command_if_writable_api_exists

def get_category(command):
    command_split = command.split()
    if len(command_split) < 2:
        return None
    return command_split[1]

def create_category_if_missing(category, reply):
    resp_code = req.get(f"{db_apis[1]}/{category}").status_code
    if resp_code == 404:
        #TODO: error handling below
        req.put(f"{db_apis[1]}/{category}")
        reply = f'Added new category: {category}\n'
    elif resp_code != 200:
        reply = f'Problem adding new category: {category}. HTTP status from db: {resp_code}\n'
    else:
        reply = ''
    return reply

def add_content(command, category, reply, help):
    content = None
    try:
        content = json.loads(command[len(category) + 6:].replace("'", "’"))
    except:
        reply = f'{reply}Could not parse content to add. Does it exists and is it valid json?\n\n{help}'
    if content != None:
        if "name" not in content.keys():
            reply = "No name in the content. Can't add this :("
        else:
            content["_id"] = content["name"].lower().replace("'", '').replace(' ' , '-')
            headers = {"Content-Type": "application/json"}
            resp = req.post(f"{writable_api}/{category}", data=str(content).replace("'", '"').replace("’", "'"), headers=headers)
            if resp.status_code == 201:
                reply = f"{reply}Added new content to the db: {content['name']}"
            else:
                reply = f'{reply}Problem adding new content to the db: {resp.status_code} :('
    return reply

def delete_content(url, reply, help):
    revision = req.get(url).json()['_rev']
    del_response_code = req.get(f'{url}?rev={revision}').status_code
    if del_response_code == 200:
        reply = f'Content deleted'
    else:
        reply = f'Problem deleting content: {del_response_code}\n\n{help}'
    return reply

def check_content_existence(url):
    content_exists_code = req.get(url).status_code
    reply = ''
    exists = True
    if content_exists_code != 200:
        exists = False
        reply = f'Problem with content: {re.sub(r":[^/].*@", ":<password-hidden>@", url)}, HTTP status code: {content_exists_code}'
        if content_exists_code == 404:
            reply += ', content does not exist'
    return reply, exists

@only_if_writable_api_exists
@only_allowed_users
async def add(update, context):
    help = 'Usage /add <category-of-the-new-thing-to-add-eg-equipment-or-monsters> <data-in-json>\nThe <data-in-json> needs to have at least name as attribute. There might be additional fields needed when displaying the newly added content. I will try to handle these in the future.\nExample: /add monsters {"name": "Peijooni", "actions": [{"name": "Claw attack", "desc": "1d6 + 2 piercing damage"}]}'
    reply = help
    category = get_category(update.message.text)
    if category == None:
        reply = f'Category was missing.\n\n{reply}'
    else:
        reply = create_category_if_missing(category, reply)
        reply = add_content(update.message.text, category, reply, help)
    await update.message.reply_text(reply)

@only_if_writable_api_exists
@only_allowed_users
async def rm(update, context):
    help = 'Usage: /rm <category-of-the-new-thing-to-add-eg-equipment-or-monsters> <name-or-index-of-the-object-to-be-deleted>'
    reply = help
    category = get_category(update.message.text)
    category_reply, category_exists = check_content_existence(f"{db_apis[1]}/{category}")
    if not category_exists:
        reply = f'{category_reply}\n\n{reply}'
    else:
        message_split = update.message.text.split()
        if len(message_split) < 3:
            reply = f'No content to delete.\n\n{reply}'
        else:
            index = message_split[2].lower().replace("'", '').replace(' ' , '-')
            content_url = f"{db_apis[1]}/{category}/{index}"
            content_reply, content_exists = check_content_existence(content_url)
            if not content_exists:
                reply = f'{content_reply}\n\n{reply}'
            else:
                reply = delete_content(content_url, reply, help)
    await update.message.reply_text(reply)

def calculate_roll(command, plus_char):
    command_components=command.replace(' ', '').replace("@luolaBot", '').split(plus_char)
    results = []
    for component in command_components:
        if re.match(r'[0-9]*d[0-9]*', component):
            component_split = component.split('d')
            for _ in range(0, int(component_split[0])):
                results.append(random.randrange(1, int(component_split[1]), 1))
        elif re.match(r'[0-9]*', component):
            results.append(int(component))
    return results

def array_to_roll_reply(roll_arr):
    return "{} ({})".format(sum(roll_arr), str(roll_arr).replace('[', '').replace(']', ''))

def generate_roll_reply(text, plus_char):
    roll_arr = calculate_roll(text, plus_char)
    return array_to_roll_reply(roll_arr)

# function to handle errors occured in the dispatcher
async def error(update, context):
    await update.message.reply_text('an error occured')

async def get_class_feature_request_json_response(session, url, class_name):
    async with session.get(url) as resp:
        resp_json = await resp.json()
        if resp_json['class']['index'] == class_name:
            return resp_json

def simple_class_feature(feat, resp_text):
    return f'{resp_text}{feat["name"]}, level: {feat["level"]}\n'

def class_feature_by_level(feat, level_map):
    if not feat['level'] in level_map.keys():
        level_map[feat['level']] = [feat['name']]
    else:
        level_map[feat['level']].append(feat['name'])
    return level_map

def loop_through_class_features(class_features, class_name, fun, iterable):
    for i in class_features:
        iterable = fun(i, iterable)
    return iterable

async def class_5e(class_name, representation):
    resp_text = f'{class_name.capitalize()}\n\n*Class features*:\n'
    all_features = req.get(f'{DND_API_URL}/features')

    class_features = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in all_features.json()["results"]:
            url = f'https://www.dnd5eapi.co{i["url"]}'
            tasks.append(asyncio.ensure_future(get_class_feature_request_json_response(session, url, class_name)))

        class_features = [ x for x in (await asyncio.gather(*tasks)) if x is not None]

    if representation == '/class-level':
        level_map = loop_through_class_features(class_features, class_name, class_feature_by_level, {})
        level_map = sorted(level_map.items())
        for k, v in level_map:
            feats = str(v).replace("[", "").replace("]", "").replace("'", "")
            resp_text = f'{resp_text}\nLevel {k}:\n{feats}\n'
    else:
        resp_text = loop_through_class_features(class_features, class_name, simple_class_feature, resp_text)

    return(resp_text)

def monster(monster_json):
    resp_text=f'*{monster_json["name"]}*\n'
    if "size" in monster_json.keys():
        resp_text=f'{resp_text}{monster_json["size"]} '
    if "type" in monster_json.keys():
        resp_text=f'{resp_text} {monster_json["type"]} '
    if "alignment" in monster_json.keys():
        resp_text=f'{resp_text}{monster_json["alignment"]}'
    resp_text=f'{resp_text}\n\n*Actions*:\n'
    for a in monster_json["actions"]:
        resp_text=f'{resp_text}*{a["name"]}*: {a["desc"]}\n'
    return(f'{resp_text}')

def equipment(rule_json):
    resp_text=f'*{rule_json["name"]}*'
    if ('desc' in rule_json.keys()) and (len(rule_json['desc']) != 0):
        rule_desc='\n'.join(rule_json['desc'])
        resp_text=f'{resp_text}\n{rule_desc}'
    if ('equipment_category' in rule_json.keys()) and ('index' in rule_json['equipment_category'].keys()):
        if rule_json['equipment_category']['index'] == 'weapon':
            if 'damage' in rule_json.keys():
                resp_text=f'{resp_text}\n{rule_json["damage"]["damage_dice"]} {rule_json["damage"]["damage_type"]["index"]} damage'
        if rule_json['equipment_category']['index'] == 'armor':
            ac_info=f'AC: {rule_json["armor_class"]["base"]}'
            if rule_json["armor_class"]["dex_bonus"]:
                ac_info=f'{ac_info} + Dex'
            if "max_bonus" in rule_json["armor_class"].keys():
                ac_info=f'{ac_info} (max {rule_json["armor_class"]["max_bonus"]})'
            resp_text=f'{resp_text}\n{ac_info}'
    if ('special' in rule_json.keys()) and (len(rule_json['special']) != 0):
        special_rules='\n'.join(rule_json['special'])
        resp_text=f'{resp_text}\n{special_rules}'
    return(resp_text)

def generic_command(rule_category, rule, rule_content_parser_func):
    errors = {}
    for api in db_apis:
        req_url = f'{api}{rule_category}/{rule}'
        logging.info(f'Making GET request to: {re.sub(r":.*@", ":<password-hidden>@", req_url)}')
        rule_response=req.get(req_url)
        if rule_response.status_code == 200:
            return(rule_content_parser_func(rule_response.json()))
        else:
            errors[re.sub(r':[^/].*@', ':<password-hidden>@', api)] = rule_response.status_code
    return(f'Could not get {rule_category} from any of the defined APIs. Got the following errors: {errors}. :(')

def parse_simple_rule(rule_json):
    rule_name=rule_json['name']
    rule_desc='There is no description for this.'
    if 'desc' in rule_json.keys():
        rule_desc='\n'.join(rule_json['desc'])
    return(f'*{rule_name}*\n{rule_desc}')

def commandify_dice_notation(text):
    dice_notation = re.compile(r'([a-zA-Z:,\.;]) \+([0-9]*)')
    text = dice_notation.sub(r'\1 /r1d20p\2', text)
    dice_notation = re.compile(r'([0-9]*d[0-9]*) \+ ([0-9]*)')
    text = dice_notation.sub(r'/r\1p\2', text)
    dice_notation = re.compile(r'([ \(])([0-9]*d[0-9]*)([ \)])')
    text = dice_notation.sub(r'\1/r\2\3', text)
    return text

# function to handle normal text
async def text(update, context):
    text_received = update.message.text
    reply_text=""
    if re.match("/r[0-9]*d[0-9]*", text_received):
        reply_text = generate_roll_reply(text_received.replace("/r", ''), 'p')
    elif text_received.startswith('/'):
        parsed_text=text_received.split(' ')
        rule_category=parsed_text[0]
        if len(parsed_text) > 1:
            rule='-'.join(parsed_text[1:]).replace('\'', '').replace('(', '').replace(')', '').replace(':', '').lower()
            if rule_category.startswith('/class'):
                update.message.reply_text('Fetching class features. This takes a moment.')
                reply_text = asyncio.run(class_5e(rule, rule_category))
            elif rule_category in ['/equipment', '/weapon', '/armor']:
                reply_text = generic_command('/equipment', rule, equipment)
            elif rule_category == '/monster':
                reply_text = generic_command(f'{rule_category}s', rule, monster)
            else:
                reply_text = generic_command(f'{rule_category}s', rule, parse_simple_rule)
        else:
            reply_text = f'No {rule_category} given.'
    if reply_text != "":
        await update.message.reply_text(commandify_dice_notation(reply_text), parse_mode='Markdown')

def parse_config(config_file):
    if exists(config_file):
        logging.info("Using config file {}".format(config_file))
        with open(config_file, 'r') as file:
            settings = yaml.safe_load(file)
            if settings == None:
                logging.error("Could not read settings file.")
                return None
            if "token" not in settings.keys():
                logging.error("No token was given in settings file.")
                return None
            if "db_apis" in settings.keys():
                for api in settings["db_apis"]:
                    if "url" not in api.keys():
                        logging.error("Some db API did not have an URL.")
                        return None
            return settings

def set_db_apis(settings):
    api_list = db_apis
    write_api = writable_api
    if ("disable_default_db_api" in settings.keys()) and (settings["disable_default_db_api"] == True):
        logging.info(f'Default database API {DND_API_URL} will be disabled')
        api_list = []
    if "db_apis" in settings.keys():
        for api in settings["db_apis"]:
            new_api=api["url"]
            logging.info("Adding a new db API: {}".format(api["url"]))
            if ("username" in api.keys()) and ("password" in api.keys()):
                new_api_split = new_api.split("://")
                new_api="{}://{}:{}@{}".format(new_api_split[0], api["username"], api["password"], new_api_split[1])
            api_list.append(new_api)
            if (write_api == None) and (api["writable"] == True):
                logging.info(f"Adding a writable DB API: {re.sub(r':[^/].*@', ':<password-hidden>@', new_api)}")
                write_api = new_api
            elif write_api != None:
                logging.info(f'There already is a writable api: {write_api}. Not adding a new one.')
    return api_list, write_api

def set_allowed_users(settings):
    if 'privileged_users' in settings.keys():
        logging.info(f'Making the following users privileged: {settings["privileged_users"]}')
        for user in settings['privileged_users']:
            allowed_users.append(user)

def main():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Config files. Defaults to luolabot.yaml on the directory from which the bot launch command is run.")
    args = parser.parse_args()
    config_file="luolabot.yaml"
    if args.config:
        config_file=args.config

    settings = parse_config(config_file)
    if settings == None:
        logging.error("Problem with settings. Exiting.")
        return

    global db_apis
    global writable_api
    db_apis, writable_api = set_db_apis(settings)
    if db_apis == []:
        logging.error("Default database API was disabled and no custom APIs were defined. There is nothing to look data from, so I'm exiting.")
        return

    set_allowed_users(settings)
    logging.info(f'Privileged users are: {allowed_users}')

    application = Application.builder().token(settings["token"]).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("rm", rm))

    # add an handler for normal text (not commands)
    application.add_handler(MessageHandler(filters.TEXT, text))

    # add an handler for errors
    application.add_error_handler(error)

    logging.info("Starting luolaBot. Press ctrl-c to stop it.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
