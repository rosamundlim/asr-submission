"""Stores path for elastic-backend directory"""

from pathlib import Path

# /asr-submission as root
BASE_PATH = Path(__file__).resolve().parent.parent.parent

# /asr
ASR = BASE_PATH / "asr"

# /asr files
CV_VALID_DEV = ASR / "cv-valid-dev.csv"

# /elastic-backend
ELASTIC_BACKEND = BASE_PATH / "elastic-backend"

# /elastic-backend files
CONFIG_FILE = ELASTIC_BACKEND / "config.yml"
ENV_FILE = ELASTIC_BACKEND / ".env"
CA_CERT = ELASTIC_BACKEND / "ca.crt"
