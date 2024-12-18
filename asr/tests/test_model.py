"""This script tests functions in asr/model.py"""

import yaml
import pytest
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from model import load_models 
from utils import paths

# Define filepaths and variables
MODEL_ARTIFACTS_PATH = paths.MODEL_ARTIFACTS
CONFIG_PATH = paths.CONFIG

with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

HUGGINGFACE_PATH = config['model']['path']
PROCESSOR_TITLE = config['model']['processor_name']
MODEL_TITLE = config['model']['model_name']

def test_load_models():
    """
    Check if load_models function returns the correct types
    """
    processor, model = load_models(HUGGINGFACE_PATH)

    assert isinstance(processor, Wav2Vec2Processor), "Expected processor to be of type \
        Wav2Vec2Processor"
    assert isinstance(model, Wav2Vec2ForCTC), "Expected model to be of type Wav2Vec2ForCTC"
    assert isinstance((processor, model), tuple), "Expected the return value to be a tuple"
