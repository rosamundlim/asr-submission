"""
Task 2d - to transcribe all 4,076 .mp3 files in cv-valid-dev (Common Voice dataset).
References: 
i. aiohttp/asyncio documentation, 
ii. https://www.twilio.com/en-us/blog/asynchronous-http-requests-in-python-with-aiohttp
iii. openai chatgpt 3.5
"""

import os
import time
import logging
import asyncio
from typing import List
import aiofiles
import aiohttp
from tqdm.asyncio import tqdm
import pandas as pd
from utils import paths, utility_functions

logging.basicConfig(level=logging.INFO,format='%(asctime)s:%(levelname)s:%(message)s')

# Define paths and variables
AUDIO_DIRECTORY = paths.CV_VALID_DEV
# RESULTS_CSV_PATH = paths.CV_VALID_DEV_CSV
RESULTS_CSV_PATH = paths.ASR
CONFIG_FILE = utility_functions.load_yaml(paths.CONFIG)
INFERENCE_URL = CONFIG_FILE['asr_api']['inference']
PING_URL = CONFIG_FILE['asr_api']['ping']

class AudioTranscriber:
    """
    Class to manage transcription of audio files using ASR inferencing API
    """
    def __init__(self,
                 audio_dir: str,
                 results_path: str,
                 inference_url: str,
                 health_url: str
    ):
        if not os.path.isdir(audio_dir):
            raise NotADirectoryError(f"Not a valid directory: {audio_dir}")
        #if not os.path.isfile(results_path):
        #    raise FileNotFoundError(f"File not found: {results_path}")
        self.audio_dir = audio_dir
        self.mp3_filenames = None
        self.check_valid_audio()
        self.results_path = results_path
        self.inference_url = inference_url
        self.health_url = health_url
        self.transcription = {'generated_text': [],
                              'duration': [],
                              'audiofile': []
                              }

    def check_valid_audio(self) -> None:
        """
        Checks the no. of valid .mp3 files in self.audio_dir
        and save the filenames to a list in self.mp3_filenames
        """
        audio_dir_files = os.listdir(self.audio_dir)
        self.mp3_filenames = [f for f in audio_dir_files if f.endswith('.mp3')]
        logging.info("Found %s .mp3 files.", len(self.mp3_filenames))
 
    async def health_check(self, session: aiohttp.ClientSession) -> None:
        """
        Makes get request for health check
        """
        async with session.get(self.health_url) as resp:
            try:
                if resp.status != 200:
                    logging.info("API Health check failed with status: %s", resp.status)
                else:
                    logging.info("API Health check status ok")
            except Exception as e:
                logging.error("Health check failed: %s", e)

    async def transcribe_single_audio(self, session: aiohttp.ClientSession, filename: str):
        """
        pass
        """
        start_time = time.perf_counter()
        audio_filepath = os.path.join(self.audio_dir, filename)
        form = aiohttp.FormData()

        async with aiofiles.open(audio_filepath, 'rb') as f:
            audio_data = await f.read()
            form.add_field('file', audio_data, filename=filename, content_type='audio/mp3')

        async with session.post(self.inference_url, data=form) as resp:
            if resp.status != 200:
                logging.error("Failed to transcribe %s : %s", filename, resp.status)
                return {
                    'generated_text': f'Error: {resp.status}',
                    'duration': f'Error: {resp.status}',
                    'audiofile': filename,
                }
            response = await resp.json()
            
            # to remove later
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            
            logging.info(f"Time taken for {filename}: {elapsed_time:.2f} seconds")
            
            return {
                'generated_text': response['transcription'],
                'duration': response['duration'],
                'audiofile': filename
            }

    async def transcribe_files_in_dir(self, session: aiohttp.ClientSession):
        """
        pass
        """
        tasks = []
        for file in self.mp3_filenames[:50]:
            tasks.append(asyncio.ensure_future(self.transcribe_single_audio(session, \
                                                                            filename=file)))
        results = await asyncio.gather(*tasks)
        #results = await tqdm.gather(*tasks, total=len(tasks), desc='Transcribing .mp3 files')

        return results
    
    def write_results(self, results: List[dict[str, str]]):
        for response in results:
            self.transcription['generated_text'].append(response['generated_text'])
            self.transcription['duration'].append(response['duration'])
            self.transcription['audiofile'].append(response['audiofile'])
        df = pd.DataFrame.from_dict(self.transcription)
        filepath = os.path.join(self.results_path, 'transcription_results.csv')
        df.to_csv(filepath, index=False)

    async def main(self):
        """
        pass
        """
        async with aiohttp.ClientSession() as session:
            await self.health_check(session)
            results = await self.transcribe_files_in_dir(session)
        
        self.write_results(results)

if __name__ == "__main__":
    #start_time = time.perf_counter()
    transcriber = AudioTranscriber(audio_dir=AUDIO_DIRECTORY,
                                   results_path=RESULTS_CSV_PATH,
                                   inference_url=INFERENCE_URL,
                                   health_url=PING_URL,
                                   )
    asyncio.run(transcriber.main())
    #end_time = time.perf_counter()
    #elapsed_time = end_time - start_time
    #logging.info('Program Duration: %.2f seconds', elapsed_time)
