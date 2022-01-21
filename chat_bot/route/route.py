from flask import Blueprint, render_template
from chat_bot.telegram_bot.chatbot import bot
import os

API_TOKEN = os.environ['API_TOKEN_BOT']

mod = Blueprint('home', __name__,
                template_folder='templates',
                static_folder='static')


@mod.route('/')
def home():
    return 'run succesfully'


@mod.route("/setwebhook")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://sard-ai.herokuapp.com/' + API_TOKEN)
    print(bot.get_webhook_info())
    print('https://sard.ai/' + API_TOKEN)
    return API_TOKEN, 200