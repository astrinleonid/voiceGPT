
import pickle
import openai
import json
import requests
import telebot

from telebot import types
import ffmpeg
import whisper
from pydub import AudioSegment
from voice_generator import Voice, Synthesizer


voice_transcription_model = whisper.load_model("large")

with open('config.json') as token_file:
    tokens = json.load(token_file)

openai.api_key = tokens['openai']
telegram_token  = tokens['telegram']
COQUI_STUDIO_TOKEN = tokens['coqui']
URL = tokens['url']
port = tokens['port']
azure_credentials = (tokens['azure'], tokens['region'])

bot = telebot.TeleBot(token=telegram_token)
file_path = 'response.wav'

with open('tts_model.pkl','rb' ) as file:
    tts = pickle.load(file)

synth = Synthesizer(file_path, tts, azure_credentials)
synth.add_voice(Voice('Leonid', 'coqui', 'kingsson.wav'))
synth.add_voice(Voice('Nof', 'coqui', 'Nof.wav'))
synth.add_voice(Voice('Sasha', 'coqui', 'sasha.wav'))
synth.add_voice(Voice('Christopher', 'azure', "en-US-ChristopherNeural"))

mode = 'chatgpt'

def return_voice_response(prompt, mode):

    if mode == 'chatgpt':
        result = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
                {"role": "user", "content": prompt}
            ]
        )
        x = result['choices'][0]['message']['content']

    else:
        x = prompt

    print(x)
    # synthesis
    synth.generate(x)
    return synth.file_path



@bot.message_handler(commands=['start'])
def start(message):
  bot.send_message(message.chat.id, '<b>Im Mac</b>', parse_mode = 'html')

@bot.message_handler(commands=['speaker'])
def get_speaker(message):
  print("Change speaker")
  all_speakers = "\n"
  for i, voice in enumerate(synth.voices):
      all_speakers += f"{i+1} {voice.name} {voice.model}\n"
  bot.send_message(message.chat.id, f'Current speaker: {synth.get_voice_name()}', parse_mode = 'html')
  bot.send_message(message.chat.id, f'Available speakers: {all_speakers}', parse_mode='html')
  sent = bot.reply_to(message, f'To change speaker, reply with speaker number', parse_mode='html')
  bot.register_next_step_handler(sent, change_speaker)

  # markup = types.KeyboardButtonPollType

@bot.message_handler(commands=['mode'])
def change_mode(message):
  print("Change mode")
  bot.send_message(message.chat.id, f'Current mode: {mode}', parse_mode='html')
  sent = bot.reply_to(message, f'Enter mode, chatgpt or parrot', parse_mode='html')
  bot.register_next_step_handler(sent, change_mode)

def change_mode(message):
    global mode
    input = message.text
    if input in ['chatgpt', 'parrot']:
        mode = input
    bot.send_message(message.chat.id, f'Current mode: {mode}', parse_mode='html')
def change_speaker(message):

    num = int(message.text)
    if num in range(synth.num_voices + 1):
        synth.set_voice(num)
        print(synth.get_voice_name())

    bot.send_message(message.chat.id, f'Current speaker: {synth.get_voice_name()}', parse_mode='html')

@bot.message_handler(content_types=['text'])
def get_user_text(message):
    print("Incoming text")

    print(message.text)
    output_file = return_voice_response(message.text, mode)
    # bot.send_message(message.chat.id, 'Audio follows', parse_mode = 'html')
    audio = open(output_file, 'rb')
    bot.send_audio(message.chat.id, audio)

@bot.message_handler(content_types=['voice'])
def get_user_voice(message):
    print("Incoming voice")
    file_id = message.voice.file_id
    file_name = f'voice_{file_id}.ogg'
    # Download the voice message file
    download_voice_file(file_id, file_name)
    print('File saved')
    result = voice_transcription_model.transcribe('voice_prompt.wav')
    prompt = " ".join([segment['text'] for segment in result['segments']])
    print(prompt)
    output_file = return_voice_response(prompt, mode)
    # bot.send_message(message.chat.id, 'Audio follows', parse_mode = 'html')
    audio = open(output_file, 'rb')
    bot.send_audio(message.chat.id, audio)

def download_voice_file(file_id, file_name):
    file_path = bot.get_file(file_id).file_path
    file_url = f'https://api.telegram.org/file/bot{telegram_token}/{file_path}'
    response = requests.get(file_url)
    # print(response)
    with open(file_name, 'wb') as f:
        f.write(response.content)
    audio = AudioSegment.from_file(file_name)
    audio.export('voice_prompt.wav', format='wav')

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=port)
    bot.polling(none_stop=True)




