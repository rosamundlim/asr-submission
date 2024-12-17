"""App module to serve FastAPI app"""

from pathlib import Path
from fastapi import FastAPI
import yaml

# Define base path and subsequent filepaths 
BASE_PATH = Path(__file__).resolve().parent.parent
OPENAPI_PATH = BASE_PATH / "docs" / "openapi.yml"

with open(OPENAPI_PATH,"r") as file:
    openapi_params = yaml.safe_load(file)

app = FastAPI(
    title=openapi_params["info"]["title"],
    description=openapi_params["info"]["description"],
    version=openapi_params["info"]["version"],
)

@app.get("/ping")
async def ping():
    """
    A health check endpoint to ensure that the API service is working
    """
    return {"message":"pong"}
