"""Stores directories and filepaths for this project to ensure modularity and reduce repetition"""

from pathlib import Path

# /asr-submission/ (project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ./asr/ directory
ASR = BASE_DIR / "asr"
CV_VALID_DEV = ASR / "cv-valid-dev"
MODEL_ARTIFACTS = ASR / "model_artifacts"
CONF = ASR / "conf"

# ./CONF/ directory
OPENAPI = CONF / "openapi.yml"
CONFIG = CONF / "config.yml"
