import requests as req
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

def class_5e(update, context):
    split_msg = update.message.text.split(' ')
    if len(split_msg) > 1:
        update.message.reply_text("Fetching class features. Ftm this takes a while.")
        class_name = ' '.join(split_msg[1:]).capitalize()
        resp_text = f'{class_name}\n\n*Class features*:\n'
        class_received = '-'.join(split_msg[1:]).lower()
        all_features = req.get(f'{DND_API_URL}/features')
        for i in all_features.json()["results"]:
            f=req.get(f'https://www.dnd5eapi.co{i["url"]}').json()
            if f['class']['index'] == class_received:
                resp_text = f'{resp_text}{f["name"]}, level: {f["level"]}\n'
        update.message.reply_text(resp_text, parse_mode='Markdown')
    else:
        update.message.reply_text("No class given.")

def monster(update, context):
    parsed_text=update.message.text.split(' ')
    if len(parsed_text) > 1:
        rule_category=parsed_text[0]
        monster='-'.join(parsed_text[1:]).replace('\'', '').replace('(', '').replace(')', '').replace(':', '').lower()
        monster_response=req.get(f'{DND_API_URL}{rule_category}s/{monster}')
        if monster_response.status_code == 200:
            monster_content=monster_response.json()
            #TODO: Should maybe check some the keys
            resp_text=f'*{monster_content["name"]}*\n{monster_content["size"]} {monster_content["type"]}, {monster_content["alignment"]}\n\n*Actions*:\n'
            for a in monster_content["actions"]:
                resp_text=f'{resp_text}*{a["name"]}*: {a["desc"]}\n'
            update.message.reply_text(f'{resp_text}', parse_mode='Markdown')
        else:
            update.message.reply_text(f'Could not get monster info from DnD API ({monster_response.status_code}). :(')
    else:
        update.message.reply_text('No monster given.')

# function to handle normal text 
def text(update, context):
    text_received = update.message.text
    if text_received.startswith('/'):
        parsed_text=text_received.split(' ')
        if parsed_text[0] not in FORBIDDEN_COMMANDS:
            rule_category=parsed_text[0]
            rule='-'.join(parsed_text[1:]).replace('\'', '').replace('(', '').replace(')', '').replace(':', '').lower()
            rule_response=req.get(f'{DND_API_URL}{rule_category}s/{rule}')
            if rule_response.status_code == 200:
                rule_content=rule_response.json()
                rule_name=rule_content['name']
                rule_desc='There is no description for this.'
                if 'desc' in rule_content.keys():
                    rule_desc='\n'.join(rule_content['desc'])
                update.message.reply_text(f'{rule_name}\n\n{rule_desc}')
            else:
                update.message.reply_text(f'Could not get rule from DnD API ({rule_response.status_code}). :(')

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
    dispatcher.add_handler(CommandHandler("class", class_5e))
    dispatcher.add_handler(CommandHandler("monster", monster))

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
