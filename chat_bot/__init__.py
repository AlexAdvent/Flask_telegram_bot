from chat_bot.telegram_bot.chatbot import bot
from chat_bot.route.route import mod as route_blueprint
from flask import Flask

def create_app():

    app = Flask(__name__)

    app.register_blueprint(route_blueprint)

    return app