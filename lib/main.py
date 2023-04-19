from flask import Flask
from flask import request
from flask import send_file
from flask import render_template
from flask import Response

import pickle

import openai
with open('openaitoken.txt') as token_file:
    openai.api_key = token_file.read()

COQUI_STUDIO_TOKEN='aexT3jUUjnq0rvbzcMVV3p74SOs398EryywqBqrNK2dhMxyD5p9ke8cR4uzcrxQn'
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


app.run(host='0.0.0.0', port=5001)



