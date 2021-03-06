import argparse
import asyncio
import aiohttp
from os.path import exists
from asyncio.coroutines import sys
import requests as req
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import time
import yaml

DND_API_URL = "https://www.dnd5eapi.co/api"

# function to handle the /start command
def start(update, context):
    update.message.reply_text('Dime do dungeon!')

# function to handle the /help command
def help(update, context):
    update.message.reply_text('''Lousy bot that spits out DnD 5e rules:
Usage:
/<rule-category> <rule>
<rule-category> can be eg. spell, condition, feature or class.
Special <rule-category> class-level allows to sort class features by level.
<rule> could be eg. the spell Hunter\'s Mark or the feature rage.
Rules given by this bot come from http://www.dnd5eapi.co/
Bot code can be found in: https://github.com/juuso22/luolaBot''')

# function to handle errors occured in the dispatcher 
def error(update, context):
    update.message.reply_text('an error occured')

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
    #TODO: Should maybe check some of the keys
    resp_text=f'*{monster_json["name"]}*\n{monster_json["size"]} {monster_json["type"]}, {monster_json["alignment"]}\n\n*Actions*:\n'
    for a in monster_json["actions"]:
        resp_text=f'{resp_text}*{a["name"]}*: {a["desc"]}\n'
    return(f'{resp_text}')

def equipment(rule_json):
    resp_text=f'*{rule_json["name"]}*'
    if len(rule_json['desc']) != 0:
        rule_desc='\n'.join(rule_json['desc'])
        resp_text=f'{resp_text}\n{rule_desc}'
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
    if len(rule_json['special']) != 0:
        special_rules='\n'.join(rule_json['special'])
        resp_text=f'{resp_text}\n{special_rules}'
    return(resp_text)

def generic_command(rule_category, rule, rule_content_parser_func):
    rule_response=req.get(f'{DND_API_URL}{rule_category}/{rule}')
    if rule_response.status_code == 200:
        return(rule_content_parser_func(rule_response.json()))
    else:
        return(f'Could not get {rule_category} from DnD API ({rule_response.status_code}). :(')

def parse_simple_rule(rule_json):
    rule_name=rule_json['name']
    rule_desc='There is no description for this.'
    if 'desc' in rule_json.keys():
        rule_desc='\n'.join(rule_json['desc'])
    return(f'*{rule_name}*\n{rule_desc}')
        
# function to handle normal text 
def text(update, context):
    text_received = update.message.text
    if text_received.startswith('/'):
        parsed_text=text_received.split(' ')
        rule_category=parsed_text[0]
        if len(parsed_text) > 1:               
            rule='-'.join(parsed_text[1:]).replace('\'', '').replace('(', '').replace(')', '').replace(':', '').lower()
            if rule_category.startswith('/class'):
                update.message.reply_text('Fetching class features. This takes a moment.')
                update.message.reply_text(asyncio.run(class_5e(rule, rule_category)), parse_mode='Markdown')
            elif rule_category in ['/equipment', '/weapon', '/armor']:
                update.message.reply_text(generic_command('/equipment', rule, equipment), parse_mode='Markdown')
            elif rule_category == '/monster':
                update.message.reply_text(generic_command(f'{rule_category}s', rule, monster), parse_mode='Markdown')
            else:
                update.message.reply_text(generic_command(f'{rule_category}s', rule, parse_simple_rule), parse_mode='Markdown')
        else:
            update.message.reply_text(f'No {rule_category} given.')

async def look_for_primary(timestamp, instances):
    if timestamp == -1:
        timestamp = time.time()
        for instance in instances:
            print(instance)
        return timestamp
    else:
        while True:
            print("I'm test output, remove me!")
            time.sleep(10)

async def run_bot(updater):
    # start your shiny new bot
    updater.start_polling()
    # run the bot until Ctrl-C
    updater.idle()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_dir", help="directory for config files")
    args = parser.parse_args()
    config_dir=''
    if args.config_dir:
        config_dir=args.config_dir
    with open('{}token.txt'.format(config_dir), 'r') as file:
        BOT_TOKEN=file.read().replace('\n', '')

    settings = None
    config_file = '{}luolabot.yaml'.format(config_dir)
    if exists(config_file):
        print("Using config file {}".format(config_file))
        with open(config_file, 'r') as file:
            settings = yaml.safe_load(file)                

    # create the updater, that will automatically create also a dispatcher and a queue to 
    # make them dialoge
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # add handlers for start and help commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))

    # add an handler for normal text (not commands)
    dispatcher.add_handler(MessageHandler(Filters.text, text))

    # add an handler for errors
    dispatcher.add_error_handler(error)

    #Primary-backup model
    #Start a thread that looks for primary
    #Check if you are the primary
    #In case you are not
    #|
    #|-If a primary is found, become backup, keep the check thread running and do nothing else
    #|-If no primary is found claim to be primary and record the timestamp
    #
    #In case you are
    #|
    #|-If a lower timestamp primary is found, become backup, keep the check thread running and do nothing else
    #|-If you turn out to be the highest primary, start idling until check thread finds lower timestamp primary

    print("Starting luolaBot. Press ctrl-c to stop it.")
    primary_role_assumption_timestamp = -1
    while True:
        instances = []
        if settings != None and 'instances' in settings.keys():
            instances = settings['instances']
        tasks=[look_for_primary(primary_role_assumption_timestamp, instances)]
        if primary_role_assumption_timestamp != -1:
            print("Node dedicated as primary with timestamp {}".format(primary_role_assumption_timestamp))
            tasks.insert(0, run_bot(updater))
        async_tasks=list(map(asyncio.create_task, tasks))
        await asyncio.wait(async_tasks, return_when=asyncio.FIRST_COMPLETED)
        primary_role_assumption_timestamp=async_tasks[0].result()

if __name__ == '__main__':
    asyncio.run(main())
