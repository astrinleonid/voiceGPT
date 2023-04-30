
import pickle
import openai
import json
import requests
import telebot
from azureSDK import synthesize_with_azure
from telebot import types
import ffmpeg
import whisper
from pydub import AudioSegment



voice_transcription_model = whisper.load_model("large")

with open('config.json') as token_file:
    tokens = json.load(token_file)

openai.api_key = tokens['openai']
telegram_token  = tokens['telegram']
COQUI_STUDIO_TOKEN = tokens['coqui']
URL = tokens['url']
port = tokens['port']
speech_key = tokens['azure']
service_region = tokens['region']

bot = telebot.TeleBot(token=telegram_token)

speakers = {'LEONID' : 'kingsson.wav',
            'NOF' : 'Nof.wav',
            'SASHA' : 'sasha.wav',
            'Aria': "en-US-AriaNeural",
            'Christopher': "en-US-ChristopherNeural"}

speaker = 'SASHA'
with open('tts_model.pkl','rb' ) as file:
    tts = pickle.load(file)
synthesizer = 'AZURE'

def return_voice_response(prompt, speaker):

    result = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
            {"role": "user", "content": prompt}
        ]
    )

    x = result['choices'][0]['message']['content']
    print(x)
    # synthesis
    file_path = 'response.wav'
    if synthesizer == 'COQUI':
        tts.tts_to_file(text=x, speaker_wav=speakers[speaker], language=tts.languages[0], file_path=file_path)
    elif synthesizer == 'AZURE':
        synthesize_with_azure(x, file_path, speech_key, service_region)
    return file_path



@bot.message_handler(commands=['start'])
def start(message):
  bot.send_message(message.chat.id, '<b>Im Mac</b>', parse_mode = 'html')

@bot.message_handler(commands=['speaker'])
def get_speaker(message):
  all_speakers = "\n" + "\n".join([name for name in speakers])
  bot.send_message(message.chat.id, f'Current speaker: {speaker}', parse_mode = 'html')
  bot.send_message(message.chat.id, f'Available speakers: {all_speakers}', parse_mode='html')
  sent = bot.reply_to(message, f'To change speaker, reply with speaker name', parse_mode='html')
  bot.register_next_step_handler(sent, change_speaker)

  # markup = types.KeyboardButtonPollType

def change_speaker(message):
    global speaker
    name = message.text
    if name in [x for x in speakers]:
        print(name)
        speaker = name
    bot.send_message(message.chat.id, f'Current speaker: {speaker}', parse_mode='html')

@bot.message_handler(content_types=['text'])
def get_user_text(message):
    print("Incoming request")

    print(message.text, speaker)
    output_file = return_voice_response(message.text, speaker)
    # bot.send_message(message.chat.id, 'Audio follows', parse_mode = 'html')
    audio = open(output_file, 'rb')
    bot.send_audio(message.chat.id, audio)

@bot.message_handler(content_types=['voice'])
def get_user_voice(message):
    file_id = message.voice.file_id
    file_name = f'voice_{file_id}.ogg'
    # Download the voice message file
    download_voice_file(file_id, file_name)
    print('File saved')
    result = voice_transcription_model.transcribe('voice_prompt.wav')
    prompt = " ".join([segment['text'] for segment in result['segments']])
    print(prompt, speaker)
    output_file = return_voice_response(prompt, speaker)
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




