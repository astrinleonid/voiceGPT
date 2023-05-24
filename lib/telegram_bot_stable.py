import pickle
import openai
import json
import requests
import telebot
import os
import platform
import pathlib
import time
from datetime import datetime

from TTS.api import TTS

import whisper
from pydub import AudioSegment
from voice_generator import Voice, Synthesizer

current_os = platform.system()
print("Current OS: ", current_os)
if current_os == "Windows":
    temp = pathlib.PosixPath
    pathlib.PosixPath = pathlib.WindowsPath

voice_transcription_model = whisper.load_model("small")

with open('config.json') as token_file:
    tokens = json.load(token_file)

openai_api_key = tokens['openai']
telegram_token = tokens['telegram']
COQUI_STUDIO_TOKEN = tokens['coqui']
URL = tokens['url']
port = tokens['port']
azure_credentials = (tokens['azure'], tokens['region'])
model = tokens['gpt_model']
available_models = {}


class ChatApp:
    def __init__(self, openai_api_key):
        # Setting the API key to use the OpenAI API
        openai.api_key = openai_api_key
        self.messages = []

    def chat(self, message):
        self.messages.append({"role": "user", "content": message})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.messages
        )
        self.messages.append({"role": "assistant", "content": response["choices"][0]["message"].content})
        return response["choices"][0]["message"]["content"]

    def new_chat(self):
        self.messages = [self.messages]
        print(f"Chat reset, messages {self.messages}")


chatGPT = ChatApp(openai_api_key)

# bot = telebot.TeleBot(token=telegram_token)

BOT_INTERVAL = 3
BOT_TIMEOUT = 5

now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
error_message = f"Bot started at {dt_string}"

def bot_polling(token=telegram_token):

     global error_message
     bot = None
     print("Starting bot polling now")
     while True:
         try:
             print("New bot instance started")
             bot = telebot.TeleBot(token) #Generate new bot instance
             botactions(bot) #If bot is used as a global variable, remove bot as an input param
             bot.polling(none_stop=True, interval=BOT_INTERVAL, timeout=BOT_TIMEOUT)
         except Exception as ex: #Error in polling
             print("Bot polling failed, restarting in {}sec. Error:\n{}".format(BOT_TIMEOUT, ex))
             now = datetime.now()
             dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
             error_message += f"\n\nCrash at {dt_string} Error message: {ex}"
             bot.stop_polling()
             time.sleep(BOT_TIMEOUT)
         else: #Clean exit
             bot.stop_polling()
             print("Bot polling loop finished")
             break #End loop


file_path = 'response'
tts = TTS(model_name='tts_models/multilingual/multi-dataset/your_tts', progress_bar=False, gpu=False)
# with open('tts_model.pkl', 'rb') as file:
#     tts = pickle.load(file)

synth = Synthesizer(file_path, tts, azure_credentials)
synth.add_voice(Voice('Leonid', 'coqui', 'kingsson.wav'))
synth.add_voice(Voice('Nof', 'coqui', 'Nof.wav'))
synth.add_voice(Voice('Sasha', 'coqui', 'sasha.wav'))
synth.add_voice(Voice('Christopher', 'azure', "en-US-ChristopherNeural"))
synth.add_voice(Voice('Jenny', 'azure', "en-US-JennyNeural"))
synth.add_voice(Voice('Aria', 'azure', "en-US-AriaNeural"))

mode = 'chatgpt'


def return_voice_response(prompt, mode):
    x = []

    if prompt[0] == "%":
        print("String is formatted, changing mode to parrot")
        mode = 'parrot'
        part = []

        words = prompt.strip('%').split()
        num_words = len(words)
        words = iter(words)
        for i in range(num_words):
            word = next(words)
            if word[0] == "%":
                # insert pause
                if len(part) > 0:
                    x.append(" ".join(part))
                    part = []
                    print(f"part reset, len(part) {len(part)}")
                x.append(word)
            else:
                part.append(word)
        x.append(" ".join(part))
    elif mode == 'chatgpt':
        try:

            # result = openai.ChatCompletion.create(
            #     model=model,
            #     messages=[
            #         {"role": "user", "content": prompt}
            #         ]
            #     )
            # x = result['choices'][0]['message']['content']
            x.append(chatGPT.chat(prompt))

        except Exception as er:
            print(f"invalid responce from openAi API, error {er} ")
            x.append("invalid response from openAi API")

    else:
        x.append(prompt)

    print(" ".join(x))

    # synthesis
    synth.generate(x)
    return synth.get_file_path()

def botactions(bot):

    @bot.message_handler(commands=['new_chat'])
    def new_chat(message):
        chatGPT.new_chat()
        bot.send_message(message.chat.id, "Start a new conversation", parse_mode='html')


    @bot.message_handler(commands=['start'])
    def start(message):
        greeting = """
            <b>Welcome to the chatGPT chatbot</b>
    
            Chatbot has three modes. 
            <b>ChatGPT mode:</b> any text or voice input is treated as a prompt for chatGPT. The response received from chatGPT API is vocalized and returned as the sound file
            <b>Parrot mode:</b> the input itself is converted to speech and returned as a sound file
            <b>Speech to text mode:</b> the voice input is converted to text
    
            To change mode: /mode
            To change speaker: /speaker
            To change chatGPT model: /model
            To add speaker: /new_speaker 
            To start a new conversation with chatGPT: /new_chat
      """
        bot.send_message(message.chat.id, greeting, parse_mode='html')


    @bot.message_handler(commands=['speaker'])
    def get_speaker(message):
        print("Change speaker")
        all_speakers = "\n"
        for i, voice in enumerate(synth.voices):
            all_speakers += f"{i + 1} {voice.name} {voice.model}\n"
        bot.send_message(message.chat.id, f'Current speaker: {synth.get_voice_name()}', parse_mode='html')
        bot.send_message(message.chat.id, f'Available speakers: {all_speakers}', parse_mode='html')
        sent = bot.reply_to(message, f'To change speaker, reply with speaker number, else reply with 0', parse_mode='html')
        bot.register_next_step_handler(sent, change_speaker)


    @bot.message_handler(commands=['new_speaker'])
    def new_speaker(message):
        print("Add new speaker")
        all_speakers = "\n"
        for i, voice in enumerate(synth.voices):
            all_speakers += f"{i + 1} {voice.name} {voice.model}\n"
        bot.send_message(message.chat.id, f'Current speaker: {synth.get_voice_name()}', parse_mode='html')
        bot.send_message(message.chat.id, f'Available speakers: {all_speakers}', parse_mode='html')
        sent = bot.reply_to(message, f"""
                                        To add your voice to the list of the speakers, send a voice message with the next phrase: 
                                        <b> Once upon a time, the King's youngest son 
                                        became filled with the desire to go abroad, and see the world. </b> 
                                        else reply with 0""",
                            parse_mode='html')
        bot.register_next_step_handler(sent, new_speaker)


    # markup = types.KeyboardButtonPollType

    @bot.message_handler(commands=['mode'])
    def change_mode(message):
        print("Change mode")
        bot.send_message(message.chat.id, f'Current mode: {mode}', parse_mode='html')
        sent = bot.reply_to(message,
                            f'Modes available:<b>\n1  chatgpt\n2  speech_to_text\n3  parrot</b>\nTo change mode send mode number, or send 0 to pass',
                            parse_mode='html')
        bot.register_next_step_handler(sent, change_mode)
        print("Mode changed")


    @bot.message_handler(commands=['model'])
    def change_model(message):
        global available_models
        print("List models")
        bot.send_message(message.chat.id, f'Current model: {model}', parse_mode='html')
        models = openai.Model.list()
        all_models = '\n'
        for i, model_name in enumerate(models.data):
            if model_name.id[:3] == 'gpt':
                all_models += f"{i + 1} {model_name.id}\n"
                available_models[i + 1] = model_name.id
        bot.send_message(message.chat.id, f'Available models: {all_models}', parse_mode='html')
        sent = bot.reply_to(message, f'To change model, reply with model number, else reply with 0', parse_mode='html')
        bot.register_next_step_handler(sent, change_model)

    @bot.message_handler(commands=['crash'])
    def crash_bot(message):

        bot.send_message(message.chat.id, f'Crashing')
        int('kjwnkjn')

    @bot.message_handler(commands=['log'])
    def crash_log(message):

        bot.send_message(message.chat.id, error_message)


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
       if mode == "speech_to_text":
           bot.send_message(message.chat.id, prompt, parse_mode='html')
       else:
           output_file = return_voice_response(prompt, mode)
           # bot.send_message(message.chat.id, 'Audio follows', parse_mode = 'html')
           audio = open(output_file, 'rb')
           bot.send_audio(message.chat.id, audio)


    def change_mode(message):
        global mode
        input = message.text
        modes = ['chatgpt', 'speech_to_text', 'parrot']
        try:
            num = int(input) - 1
            if num in range(3):
                mode = modes[num]
        except:
            pass
        bot.send_message(message.chat.id, f'Current mode: {mode}', parse_mode='html')


    def change_speaker(message):
        try:
            num = int(message.text)
            if num in range(synth.num_voices + 1):
                if num > 0:
                    synth.set_voice(num)
                    print(synth.get_voice_name())
        except:
            pass
        bot.send_message(message.chat.id, f'Current speaker: {synth.get_voice_name()}', parse_mode='html')


    def new_speaker(message):
        print(message.content_type)
        if message.content_type == 'voice':
            print("Voice sample received")
            file_id = message.voice.file_id
            file_name = f'voice_{file_id}.ogg'
            # Download the voice message file
            download_voice_file(file_id, file_name, 'voice_sample.wav')
            print('File saved')
            sent = bot.send_message(message.chat.id, f"Please enter the name of the speaker or enter 'quit' to abandon",
                                    parse_mode='html')
            bot.register_next_step_handler(sent, add_speaker_to_the_list)
        else:
            bot.send_message(message.chat.id, f'Current speaker: {synth.get_voice_name()}', parse_mode='html')


    def add_speaker_to_the_list(message):
        speaker_name = message.text
        if speaker_name == 'quit':
            # delete voice sample
            return
        if len(speaker_name.split()) == 1 and speaker_name.isalnum():
            # rename voice sample
            sample_file_name = speaker_name.lower() + '.wav'
            os.rename('voice_sample.wav', sample_file_name)
            synth.add_voice(Voice(speaker_name, 'coqui', sample_file_name))
            sent = bot.send_message(message.chat.id, f"Speaker added",
                                    parse_mode='html')
        else:
            sent = bot.send_message(message.chat.id,
                                    f"The name is not valid, should be one word, use alphanumeric symbols only",
                                    parse_mode='html')
            sent = bot.send_message(message.chat.id, f"Please enter the name of the speaker or enter 'quit' to abandon",
                                    parse_mode='html')
            bot.register_next_step_handler(sent, add_speaker_to_the_list)


    def change_model(message):
        global model
        try:
            num = int(message.text)
            if num in available_models:
                model = available_models[num]
                print(model)
        except:
            pass
        bot.send_message(message.chat.id, f'Current model: {model}', parse_mode='html')



    def download_voice_file(file_id, file_name, output_file='voice_prompt.wav'):
        file_path = bot.get_file(file_id).file_path
        file_url = f'https://api.telegram.org/file/bot{telegram_token}/{file_path}'
        response = requests.get(file_url)
        # print(response)
        with open(file_name, 'wb') as f:
            f.write(response.content)
        audio = AudioSegment.from_file(file_name)
        audio.export(output_file, format='wav')


if __name__ == '__main__':
    # polling_thread = threading.Thread(target=bot_polling)
    # polling_thread.daemon = True
    # polling_thread.start()
    # app.run(host='0.0.0.0', port=port)
    bot_polling(telegram_token)
    # while True:
    #     try:
    #         time.sleep(120)
    #     except KeyboardInterrupt:
    #         break



