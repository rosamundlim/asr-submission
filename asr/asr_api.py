"""App module to serve FastAPI app"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from utils import paths, utility_functions
# import sys

logging.basicConfig(level=logging.INFO,format='%(asctime)s:%(levelname)s:%(message)s')

# Define filepaths
OPENAPI_PATH = paths.OPENAPI
CONFIG_PATH = paths.CONFIG

# Define config, variables, params
openapi_params = utility_functions.load_yaml(OPENAPI_PATH)
config = utility_functions.load_yaml(CONFIG_PATH)
model_path = config['model']['path']
sampling_freq = config['audio']['sampling_frequency']

asr_model = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load model upon api setup
    """
    asr_model["processor"], asr_model["model"] = utility_functions.load_asr_model(path=model_path)
    logging.info("Wav2Vec Models loaded successfully.")
    yield
    asr_model.clear()

app = FastAPI(lifespan=lifespan,
    title=openapi_params["info"]["title"],
    description=openapi_params["info"]["description"],
    version=openapi_params["info"]["version"],
)
if not app.openapi_schema:
    app.openapi_schema = openapi_params

@app.get("/ping")
async def ping():
    """
    A health check endpoint to ensure that the API service is working
    """
    return {"message":"pong"}

class AsrResponse(BaseModel):
    """
    Defining the data validation for response fields for /asr post request
    """
    transcription: str
    duration: str

@app.post("/asr", response_model=AsrResponse)
async def asr(file: UploadFile = File(...)):
    """
    Wav2Vec model inferencing for ASR tasks.
    It takes in the raw .mp3 file, resamples it to sampling_freq
    set by user, tokenizes and makes a prediction. 
    It returns transcription (str) of the .mp3 file and the duration
    of the uploaded .mp3 file (this would imply the duration of the 
    file before resampling).
    """
    if not file.filename.endswith('.mp3'):
        raise HTTPException(status_code=400, detail='File format must be .mp3')
    try:
        y_16, duration = utility_functions.process_audio(file.file, sampling_freq)

        tokenized_input = utility_functions.tokenize_audio(y_16,
                                                 asr_model["processor"],
                                                 sampling_freq,
        )

        transcription = utility_functions.make_prediction(asr_model['model'],
                                                          asr_model["processor"],
                                                          tokenized_input,
        )

        return {"transcription": transcription, "duration": str(duration)}

    except Exception as e:
        return {"error": str(e)}
