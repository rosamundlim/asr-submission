"""
Task 2d - to transcribe all 4,076 .mp3 files in cv-valid-dev (Common Voice dataset).
References:
i. aiohttp/asyncio documentation,
ii. https://www.twilio.com/en-us/blog/asynchronous-http-requests-in-python-with-aiohttp
iii. openai chatgpt 3.5
"""

import os
import time
from datetime import datetime
import csv
import logging
import asyncio
from typing import List
import aiofiles
import aiohttp
from tqdm.asyncio import tqdm
from utils import paths, utility_functions

# Define paths and variables
AUDIO_DIRECTORY = paths.CV_VALID_DEV
RESULTS_CSV_PATH = paths.CV_VALID_DEV_CSV
CONFIG_FILE = utility_functions.load_yaml(paths.CONFIG)
INFERENCE_URL = CONFIG_FILE['asr_api']['inference']
PING_URL = CONFIG_FILE['asr_api']['ping']
TCP_LIMIT = CONFIG_FILE['cv-decode']['aiohttp_tcp_connectors']
TIMEOUT_LIMIT = CONFIG_FILE['cv-decode']['aiohttp_timeout']
SEMAPHORE_LIMIT = CONFIG_FILE['cv-decode']['semaphore_limit']

# Set logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s'
                    )

class AudioTranscriber:
    """
    Class to manage transcription of audio files using ASR inferencing API
    """
    def __init__(self,
                 audio_dir: str,
                 results_path: str,
                 inference_url: str,
                 health_url: str,
                 tcp_limit: int = TCP_LIMIT,
                 timeout_limit: int = TIMEOUT_LIMIT,
                 semaphore_limit: int = SEMAPHORE_LIMIT
    ):
        if not os.path.isdir(audio_dir):
            raise NotADirectoryError(f"Not a valid directory: {audio_dir}")
        if not os.path.isfile(results_path):
            raise FileNotFoundError(f"File not found: {results_path}")
        self.audio_dir = audio_dir
        self.results_path = results_path
        self.mp3_filenames = None
        self.check_valid_audio()
        self.inference_url = inference_url
        self.health_url = health_url
        self.tcp_limit = tcp_limit
        self.timeout_limit = timeout_limit
        self.semaphore_limit = semaphore_limit

    def check_valid_audio(self) -> None:
        """
        Checks the no. of valid .mp3 files in self.audio_dir
        and save the filenames to a list in self.mp3_filenames
        """
        audio_dir_files = os.listdir(self.audio_dir)
        self.mp3_filenames = [f for f in audio_dir_files if f.endswith('.mp3')]
        logging.info("Found %s .mp3 files.", len(self.mp3_filenames))
        required_files = set()

        with open(self.results_path, 'r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            _ = next(reader) #skip header
            for row in reader:
                filename_col = row[0]
                extracted_filename = os.path.basename(filename_col)
                required_files.add(extracted_filename)

        missing_filenames = required_files - set(self.mp3_filenames)
        if missing_filenames:
            raise ValueError(f"Missing .mp3 files: {missing_filenames}")
        logging.info("No missing .mp3 files")

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
                }

            response = await resp.json()

            return {
                'generated_text': response['transcription'],
                'duration': response['duration'],
            }

    async def transcribe_files_in_dir(self, session: aiohttp.ClientSession):
        """
        pass
        """
        semaphore = asyncio.Semaphore(self.semaphore_limit)
        tasks = []

        async def transcribe_with_limit(file):
            async with semaphore:
                return await self.transcribe_single_audio(session, filename=file)

        for file in self.mp3_filenames:
            tasks.append(asyncio.ensure_future(transcribe_with_limit(file)))

        results = await tqdm.gather(*tasks, total=len(tasks), desc='Transcribing .mp3 files')
        logging.info("Completed %s transcription tasks", len(tasks))

        return results

    def write_results(self, results: List[dict[str, str]]):
        parent_dir, filename = os.path.split(self.results_path)
        temp_path = os.path.join(parent_dir, filename + '_temp')

        logging.info('Writing results to: %s', self.results_path)
        with open(self.results_path, 'r', encoding='utf-8') as infile, \
            open(temp_path, 'w', encoding='utf-8', newline='') as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            header = next(reader)
            header.extend(['generated_text', 'duration'])
            writer.writerow(header)

            for row, result in zip(reader, results):
                if row:
                    row.extend([result.get('generated_text', 'Null'),
                                result.get('duration','Null')]
                                )
                    writer.writerow(row)
        os.replace(temp_path, self.results_path)

    async def main(self):
        """
        pass
        """
        connector = aiohttp.TCPConnector(limit=self.tcp_limit)
        timeout = aiohttp.ClientTimeout(total=self.timeout_limit)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            await self.health_check(session)
            results = await self.transcribe_files_in_dir(session)

        self.write_results(results)

if __name__ == "__main__":
    start_time = time.perf_counter()
    transcriber = AudioTranscriber(audio_dir=AUDIO_DIRECTORY,
                                   results_path=RESULTS_CSV_PATH,
                                   inference_url=INFERENCE_URL,
                                   health_url=PING_URL,
                                   )
    asyncio.run(transcriber.main())
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    logging.info('Program Duration: %.2f seconds', elapsed_time)
