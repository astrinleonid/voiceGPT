from azureSDK import synthesize_with_azure

class Voice:
    def __init__(self, name, model = 'coqui', path = ''):
        self.name = name
        self.model = model
        self.path = path

generate = Voice('Generic', 'azure', 'en-US-AIGenerate1Neural')

class Synthesizer:
    def __init__(self, file_path, tts_model, azure_credentials):
        self.voices = [generate]
        self.model = 'azure'
        self.voice = 0
        self.num_voices = 1
        self.tts = tts_model
        self.speech_key, self.service_region = azure_credentials
        self.file_path = file_path


    def add_voice(self, voice):
        self.voices.append(voice)
        self.num_voices += 1
        self.set_voice(self.num_voices - 1)

    def set_voice(self, n):
        n -= 1
        if n in range(self.num_voices):
            self.voice = n

    def get_model(self):
        return self.voices[self.voice].model

    def get_voice_name(self):
        return self.voices[self.voice].name

    def get_path(self):
        return self.voices[self.voice].path

    def generate(self, text):
        model = self.get_model()
        if model == 'coqui':
            print("Generating with coqui")
            self.tts.tts_to_file(text=text,
                                       speaker_wav=self.get_path(),
                                       language=self.tts.languages[0],
                                       file_path=self.file_path)
        elif model == 'azure':
            print("Generating with azure")
            synthesize_with_azure(text, self.file_path, self.speech_key, self.service_region, voice = self.get_path())