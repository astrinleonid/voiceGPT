
from TTS.api import TTS
import pickle

COQUI_STUDIO_TOKEN='aexT3jUUjnq0rvbzcMVV3p74SOs398EryywqBqrNK2dhMxyD5p9ke8cR4uzcrxQn'


tts_tp = TTS(model_name='tts_models/multilingual/multi-dataset/your_tts', progress_bar=False, gpu=False)

with open('tts_model.pkl','wb' ) as file:
    pickle.dump(tts_tp, file)
