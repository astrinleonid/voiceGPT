
import azure.cognitiveservices.speech as speechsdk

# Creates an instance of a speech config with specified subscription key and service region.
# Replace with your own subscription key and service region (e.g., "westus").
# c

def synthesize_with_azure(text, path, speech_key, service_region, voice = "en-US-AriaNeural"):
    print(speech_key)
    print(service_region)
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=path)
    # Set the voice name, refer to https://aka.ms/speech/voices/neural for full list.
    speech_config.speech_synthesis_voice_name = voice

    # Creates a speech synthesizer using the default speaker as audio output.
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_synthesizer.speak_text_async(text).get()

    # Checks result.
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized to speaker for text [{}]".format(text))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
        print("Did you update the subscription info?")
    # </code>