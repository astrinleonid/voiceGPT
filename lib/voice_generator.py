from azureSDK import synthesize_with_azure
from pydub import AudioSegment

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
        self.partial_files = []


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

    def generate_part(self, text, num):
        model = self.get_model()
        part_file = self.file_path + str(num)
        if model == 'coqui':
            print("Generating with coqui")
            self.tts.tts_to_file(text=text,
                                       speaker_wav=self.get_path(),
                                       language=self.tts.languages[0],
                                       file_path=part_file)
        elif model == 'azure':
            print("Generating with azure")
            synthesize_with_azure(text, part_file, self.speech_key, self.service_region, voice = self.get_path())
        self.partial_files.append(part_file)

    def generate_silence(self, length, num):
        part_file = self.file_path + str(num)
        silence = AudioSegment.silent(duration=length)
        silence.export(part_file)
        self.partial_files.append(part_file)

    def generate(self,parts):
        self.partial_files = []
        print("Generating the parts: ")
        print(parts)
        for i, part in enumerate(parts):
            if part[0] == '%':
                try:
                    length = int(part[1:])
                    print(f"Adding silence {length} ms")
                    self.generate_silence(length)

                except:
                    print("Wrong format")
            else:
                self.generate_part(part,i)

        self.merge_parts()


    def merge_parts(self):
        data = []
        response = AudioSegment.silent(duration=10)
        for infile in self.partial_files:
            response += AudioSegment.from_wav(infile)

        response.export(self.file_path, format="wav")