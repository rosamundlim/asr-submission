"""This script defines helper functions to reduce repetition"""

import yaml
import logging
import librosa
import torch
import numpy.typing as npt
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

logging.basicConfig(level=logging.INFO,format='%(asctime)s:%(levelname)s:%(message)s')

def load_yaml(path: str) -> dict:
    """
    Loads and parses a YAML file from the specified path.

    Args:
        path (str): The path to the YAML file to be loaded.

    Returns:
        dict: The parsed YAML content as a Python dictionary. 
              If the content is a list or other type, it will still be returned, 
              but the type hint assumes a dictionary for simplicity.
    
    Raises:
        FileNotFoundError: If the specified file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.
        UnicodeDecodeError: If the file cannot be decoded using UTF-8.
    """
    with open(path, 'r', encoding='UTF8') as file:
        yaml_file = yaml.safe_load(file)
        return yaml_file

def load_asr_model(path: str) -> tuple[Wav2Vec2Processor, Wav2Vec2ForCTC]:
    """
    Loads a Wav2Vec2 ASR processor and model from the specified path.

    Args:
        path (str): Path to the pre-trained Wav2Vec2 model.

    Returns:
        tuple[Wav2Vec2Processor, Wav2Vec2ForCTC]: The processor and model objects.
    """
    processor = Wav2Vec2Processor.from_pretrained(path)
    model = Wav2Vec2ForCTC.from_pretrained(path)

    return processor, model

def process_audio(path: str, sampling_freq: int) -> tuple[npt.NDArray, float]:
    """
    Processes an audio file by loading, resampling, and calculating its duration.

    Args:
        path (str): Path to the audio file.
        sampling_freq (int): Target sampling frequency to resample the audio.

    Returns:
        tuple[npt.NDArray, float]: A tuple containing the resampled audio signal 
            as a NumPy array and the duration of the audio in seconds, rounded to one 
            decimal place.
    """
    y, sample_rate = librosa.load(path)
    duration = round(librosa.get_duration(y=y,sr= sample_rate),1)
    y_16 = librosa.resample(y,
                            orig_sr=sample_rate,
                            target_sr = sampling_freq,
    )
    return y_16, duration

def tokenize_audio(y_16: npt.NDArray,
                   processor: Wav2Vec2Processor,
                   sampling_freq: int
    ) -> torch.Tensor:
    model_input = processor(y_16,
                            sampling_rate=sampling_freq,
                            return_tensors='pt',
                            padding='longest'
    ).input_values

    return model_input

def make_prediction(model: Wav2Vec2ForCTC, 
                    processor: Wav2Vec2Processor,
                    model_input: torch.Tensor) -> str:
    logits = model(model_input).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]

    return transcription
