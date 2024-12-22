
# Deploying Automatic Speech Recognition (ASR) Model to transcribe .mp3 audio files

## Introduction

In this project, I deploy Facebook's wav2vec2-large-90h model (henceforth referred as 'Wav2vec2'), an automatic speech recognition (ASR) model, to transcribe 4,076 .mp3 audio files from the Common Voice Dataset. Note that Wav2vec2 is pretrained and fine-tuned on Librispeech dataset on 16kHz sampled speech audio.


## Techstack

Note that for this project, I am using Python 3.11.11

- Basic: Python, CLI, Git Bash
- AI/ML Libraries: Transformers, Torch
- Audio: Librosa
- Deployment: FastAPI, Docker
- Testing: PyTest
- Others: asyncio, aiohttp, aiofiles, pydantic, pyYaml, git version control


## Directory Structure
```
.
└── asr-submission/
    ├── asr/
    │   ├── conf/
    │   │   ├── config.yml
    │   │   └── openapi.yml
    │   ├── cv-valid-dev/
    │   ├── logs/
    │   ├── notebooks/
    │   │   └── inference.ipynb
    │   ├── tests/
    │   │   ├── __init__.py
    │   │   └── test_utility_functions.py
    │   ├── utils/
    │   │   ├── __init__,py
    │   │   ├── paths.py
    │   │   └── utility_functions.py
    │   ├── asr_api.py
    │   ├── cv-decode.py
    │   └── cv-valid-dev.csv
    ├── .gitignore
    ├── README.md
    └── requirements.txt
```

- conf: stores config files, including config.yml, keeps all important hyperparameters and variables in a single place and avoid hard coding into individual scripts
- cv-valid-dev: stores the 4,076 .mp3 files (folder ignored in .gitignore)
- logs: keeps logfiles for cv-decode.py. Subfolders represent date (YYYY-MM-DD); files represent time (HH-MM-SS) program started running. 
- notebooks: contains inference.ipynb, which experiments with Hugging Face's inferencing pipeline tutorial. 
- tests: contains test scripts using pytest framework
- utils: paths.py is the centralized repository of all filepaths used in .py script to avoid hardcoding, utility_functions for helper functions for modularity. 
- asr_api.py: python script for serving FastAPI endpoints
- cv-decode.py: python script to automate API request to transcribe 4,076 .mp3 files in cv-valid-dev folder.
- cv-valid-dev.csv: ground truth labels for each .mp3 file. will be overwritten to include new columns for 'transcription' (ASR prediction) and 'duration'. 
- requirements.txt: shows list of all require libraries and their versions 
