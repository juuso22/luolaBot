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
    update.message.reply_text('''Usage:
/<rule-category> <rule>
<rule-category> can be eg. spell, condition or feature.
<rule> could be eg. the spell Hunter\'s Mark or the feature rage.
DnD 5e rules used by this bot come from http://www.dnd5eapi.co/''')

# function to handle errors occured in the dispatcher 
def error(update, context):
    update.message.reply_text('an error occured')

# function to handle normal text 
def text(update, context):
    text_received = update.message.text
    if text_received.startswith('/'):
        parsed_text=text_received.split(' ')
        if parsed_text[0] not in FORBIDDEN_COMMANDS:
            rule_category=parsed_text[0]
            rule='-'.join(parsed_text[1:]).replace('\'', '').lower()
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
