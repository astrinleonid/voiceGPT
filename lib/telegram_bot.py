# from flask import Flask
# from flask import request
# from flask import send_file
# from flask import render_template
import pickle
import openai
import json
#import asyncio
# import requests
# from flask import Response
# from telegram import Update, Bot
# from telegram.ext import Updater, CommandHandler, MessageHandler, filters
import telebot
from telebot import types
#last revision

with open('config.json') as token_file:
    tokens = json.load(token_file)

openai.api_key = tokens['openai']
telegram_token  = tokens['telegram']
COQUI_STUDIO_TOKEN = tokens['coqui']
URL = tokens['url']
port = tokens['port']

bot = telebot.TeleBot(token=telegram_token)

# async def set_telegram_webhook(bot, url):
#     await bot.set_webhook(url=url)
#
# asyncio.run(set_telegram_webhook(bot, f'http://{URL}:{port}/{telegram_token}'))


speakers = {'LEONID' : 'kingsson.wav', 'NOF' : 'Nof.wav', 'SASHA' : 'sasha.wav'}
speaker = speakers['LEONID']
with open('tts_model.pkl','rb' ) as file:
    tts = pickle.load(file)


def return_voice_response(prompt, speaker):

    result = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
            {"role": "system", "content": "You are a girlfriend who is not feeling well."},
            {"role": "user", "content": prompt}

        ]
    )

    x = result['choices'][0]['message']['content']
    print(x)
    # synthesis
    file_path = 'response.wav'
    tts.tts_to_file(text=x, speaker_wav=speaker, language=tts.languages[0], file_path=file_path)
    # return tts.tts(text=x, speaker_wav=speaker, language=tts.languages[0])
    return file_path


# app = Flask(__name__)
#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
#
# @app.route("/get_response")
# def get_response():
#     print("Incoming request")
#     prompt = (request.args.get("prompt"))
#     speaker = speakers[request.args.get("speaker")]
#     output_file = return_voice_response(prompt, speaker)
#     headers = {"Content-Disposition": f"attachment; filename=response.wav"}
#     return send_file(output_file, mimetype='audio/wav', as_attachment=True)


# updater = Updater(telegram_token, use_context=True)
# dispatcher = updater.dispatcher

# def handle_text(update, context):
#     # You can replace this part with your own logic to generate a response
#     response_text = f'You said: {update.message.text}'
#     context.bot.send_message(chat_id=update.message.chat_id, text=response_text)
#
# text_handler = MessageHandler(filters.text, handle_text)
# dispatcher.add_handler(text_handler)
#
# @app.route(f'/{telegram_token}', methods=['POST'])
# def handle_telegram_update():
#     update = Update.de_json(request.get_json(force=True), updater.bot)
#     dispatcher.process_update(update)
#     return 'ok'

@bot.message_handler(commands=['start'])
def start(message):
  bot.send_message(message.chat.id, '<b>Im Mac</b>', parse_mode = 'html')

@bot.message_handler(commands=['speaker'])
def start(message):
  bot.send_message(message.chat.id, f'Current speaker: {speaker}', parse_mode = 'html')
  markup = types.KeyboardButtonPollType

@bot.message_handler(content_types=['text'])
def get_user_text(message):
    print("Incoming request")

    # speaker = speakers[request.args.get("speaker")]
    speaker = speakers['LEONID']
    print(message, speaker)
    output_file = return_voice_response(message.text, speaker)
    # bot.send_message(message.chat.id, 'Audio follows', parse_mode = 'html')
    audio = open(output_file, 'rb')
    bot.send_audio(message.chat.id, audio)


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=port)
    bot.polling(none_stop=True)




