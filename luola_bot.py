import asyncio
import requests as req
import aiohttp
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

DND_API_URL = "https://www.dnd5eapi.co/api"
with open('forbidden-commands.txt', 'r') as file:
    FORBIDDEN_COMMANDS=file.read().split('\n')

# function to handle the /start command
def start(update, context):
    update.message.reply_text('Aletaas luolaamaan!')

# function to handle the /help command
def help(update, context):
    update.message.reply_text('''Lousy bot that spits out DnD 5e rules:
Usage:
/<rule-category> <rule>
<rule-category> can be eg. spell, condition or feature.
<rule> could be eg. the spell Hunter\'s Mark or the feature rage.
Rules given by this bot come from http://www.dnd5eapi.co/
Bot code can be found in: https://github.com/juuso22/luolaBot''')

# function to handle errors occured in the dispatcher 
def error(update, context):
    update.message.reply_text('an error occured')

async def get_request_json_response(session, url):
    async with session.get(url) as resp:
        return await resp.json()

async def class_5e(class_name):
    resp_text = f'{class_name.capitalize()}\n\n*Class features*:\n'
    all_features = req.get(f'{DND_API_URL}/features')

    class_features = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in all_features.json()["results"]:
            url = f'https://www.dnd5eapi.co{i["url"]}'
            tasks.append(asyncio.ensure_future(get_request_json_response(session, url)))

        class_features = await asyncio.gather(*tasks)

    for i in class_features:
        if i['class']['index'] == class_name:
            resp_text = f'{resp_text}{i["name"]}, level: {i["level"]}\n'
    
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
        if rule_json["armor_class"]["max_bonus"] != None:
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
        if parsed_text[0] not in FORBIDDEN_COMMANDS:
           rule_category=parsed_text[0]
           if len(parsed_text) > 1:               
               rule='-'.join(parsed_text[1:]).replace('\'', '').replace('(', '').replace(')', '').replace(':', '').lower()
               if rule_category == '/class':
                   update.message.reply_text('Fetching class features. This takes a while.')
                   update.message.reply_text(asyncio.run(class_5e(rule)), parse_mode='Markdown')
               elif rule_category in ['/equipment', '/weapon', '/armor']:
                   update.message.reply_text(generic_command('/equipment', rule, equipment), parse_mode='Markdown')
               elif rule_category == '/monster':
                   update.message.reply_text(generic_command(f'{rule_category}s', rule, monster), parse_mode='Markdown')
               else:
                  update.message.reply_text(generic_command(f'{rule_category}s', rule, parse_simple_rule), parse_mode='Markdown')
           else:
               update.message.reply_text(f'No {rule_category} given.')

def main():
    with open('token.txt', 'r') as file:
        BOT_TOKEN=file.read().replace('\n', '')

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

    # start your shiny new bot
    print("Starting luolaBot. Press ctrl-c to stop it.")
    updater.start_polling()

    # run the bot until Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
