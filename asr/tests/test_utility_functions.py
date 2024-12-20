"""Script for conducting unit testing for utility_functions.py using PyTest Framework"""

from utils import utility_functions
import warnings
import yaml
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import numpy as np
import librosa

def test_load_yml(tmp_path) -> None:
    """
    Tests `load_yaml` to ensure it correctly parses a YAML file.

    Args:
        tmp_path (pathlib.Path): Temporary directory for creating a sample YAML file.

    Raises:
        AssertionError: If the parsed YAML content does not match `sample_config`.
    """
    sample_config = {
        'key1': 'value1',
        'key2': 2,
        'key3': {
            'subkey1': 'subvalue1',
            'subkey2': [1, 2, 3]
        }
    }

    config_file = tmp_path / "config.yaml"
    with config_file.open('w') as f:
        yaml.safe_dump(sample_config, f)

    loaded_config = utility_functions.load_yaml(str(config_file))

    assert loaded_config == sample_config, \
        "Should correctly parse the YAML config file and return the dictionary"

def test_create_directory(tmp_path) -> None:
    """    
    Verifies that the `create_logging_directory` function in utility_functions.py
    successfully creates a new directory at the specified path.

    Args:
        tmp_path (pathlib.Path): Temporary directory path provided by pytest.
    
    Assertions:
        - The directory specified by `test_path` exists.
        - The directory specified by `test_path` is a directory (not a file).
    """
    test_path = tmp_path / "new_folder"
    utility_functions.create_logging_directory(test_path)
    assert test_path.exists() and test_path.is_dir()

def test_load_asr_model():
    """
    Tests `load_asr_model` to ensure it loads the correct ASR model and processor.

    Raises:
        AssertionError: If `model` is not a Wav2Vec2ForCTC or 
                        `processor` is not a Wav2Vec2Processor.
    """
    model_path = 'facebook/wav2vec2-large-960h'

    processor, model = utility_functions.load_asr_model(model_path)

    assert isinstance(model, Wav2Vec2ForCTC), "Should load Wav2Vec2ForCTC"
    assert isinstance(processor, Wav2Vec2Processor), "Should load Wav2Vec2Processor"

def test_process_audio():
    """
    Tests `process_audio` to ensure it processes audio correctly.

    Suppresses DeprecationWarnings from `librosa` and `audioread`.

    Raises:
        AssertionError: If `y_16` is not a NumPy array or `duration` is not a float.
    """
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='librosa.util.files')
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='librosa.core.intervals')
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='audioread.rawread')

    path = librosa.ex('trumpet')
    y_16, duration = utility_functions.process_audio(path)
    assert isinstance(y_16, np.ndarray), "Should return a Numpy.NDArray"
    assert isinstance(duration, float), "Should return a float"
