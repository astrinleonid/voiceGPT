from flask import Flask
from flask import request
from flask import send_file
from flask import render_template
import pickle
import openai
import json
import requests
from flask import Response
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, filters


with open('config.json') as token_file:
    tokens = json.load(token_file)

openai.api_key = tokens['openai']
telegram_token  = tokens['telegram']
COQUI_STUDIO_TOKEN = tokens['coqui']

speakers = {'LEONID' : 'kingsson.wav', 'NOF' : 'Nof.wav', 'SASHA' : 'sasha.wav'}

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
    # synthesis
    file_path = 'response.wav'
    tts.tts_to_file(text=x, speaker_wav=speaker, language=tts.languages[0], file_path=file_path)
    # return tts.tts(text=x, speaker_wav=speaker, language=tts.languages[0])
    return file_path


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route("/get_response")
def get_response():
    print("Incoming request")
    prompt = (request.args.get("prompt"))
    speaker = speakers[request.args.get("speaker")]
    output_file = return_voice_response(prompt, speaker)
    headers = {"Content-Disposition": f"attachment; filename=response.wav"}
    return send_file(output_file, mimetype='audio/wav', as_attachment=True)


updater = Updater(token=telegram_token, use_context=True)
dispatcher = updater.dispatcher

def handle_text(update, context):
    # You can replace this part with your own logic to generate a response
    response_text = f'You said: {update.message.text}'
    context.bot.send_message(chat_id=update.message.chat_id, text=response_text)

text_handler = MessageHandler(filters.text, handle_text)
dispatcher.add_handler(text_handler)

@app.route(f'/{telegram_token}', methods=['POST'])
def handle_telegram_update():
    update = Update.de_json(request.get_json(force=True), updater.bot)
    dispatcher.process_update(update)
    return 'ok'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)





