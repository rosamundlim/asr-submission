"""
Script to transcribe all 4,076 .mp3 files in cv-valid-dev (Common Voice dataset).
References:
i. aiohttp/asyncio documentation,
ii. https://www.twilio.com/en-us/blog/asynchronous-http-requests-in-python-with-aiohttp
iii. openai chatgpt 3.5 for generating docstrings in Google Style and facilitate debugging process. 
"""

import os
import sys
import time
import datetime
import csv
import logging
import asyncio
from typing import List
import aiofiles
import aiohttp
from tqdm.asyncio import tqdm
from asr_utils import paths, utility_functions

# Define paths and variables
AUDIO_DIRECTORY = paths.CV_VALID_DEV
RESULTS_CSV_PATH = paths.CV_VALID_DEV_CSV
CONFIG_FILE = utility_functions.load_yaml(paths.CONFIG)
INFERENCE_URL = CONFIG_FILE['asr_api']['inference']
PING_URL = CONFIG_FILE['asr_api']['ping']
TCP_LIMIT = CONFIG_FILE['cv-decode']['aiohttp_tcp_connectors']
TIMEOUT_LIMIT = CONFIG_FILE['cv-decode']['aiohttp_timeout']
SEMAPHORE_LIMIT = CONFIG_FILE['cv-decode']['semaphore_limit']

date = datetime.date.today().isoformat()
LOGFILE_DIR = paths.LOGS / date

# Set logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

utility_functions.create_logging_directory(LOGFILE_DIR)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

CURRENT_TIME = str(time.strftime("%H-%M-%S")) + '.log'
file_handler = logging.FileHandler(LOGFILE_DIR / CURRENT_TIME)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

class AudioTranscriber:
    """
    Class to manage transcription of audio files using ASR inferencing API.
    
    Validates audio files, initiates requests to an ASR API, and processes the transcription 
    results for further analysis or storage.

    Attributes:
        audio_dir (str): The directory containing audio files (.mp3) to be transcribed.
        results_path (str): The path to the CSV file with ground truth labels and where 
            transcription results are stored.
        inference_url (str): The URL of the ASR inference API endpoint.
        health_url (str): The URL to check the health status of the ASR API.
        tcp_limit (int): The TCP connection limit for API requests.
        timeout_limit (int): The timeout limit for API requests.
        semaphore_limit (int): The concurrency limit for API requests.
    
    Methods:
        check_valid_audio(): Validates .mp3 files in self.audio_dir, checks for missing files
        against self.results_path. 
        health_check(session): Checks health status of asr_api.
        transcribe_single_audio(session, filename): Transcribes a single .mp3 audio file. 
        transcribe_files_in_dir(session): Transcribes all .mp3 audio files in self.audio_dir
        write_results(results): Writes `transcription` and `duration` of .mp3 file to .csv file. 
        main(): Orchestrates the transcription workflow. 

    """
    def __init__(self,
                 audio_dir: str,
                 results_path: str,
                 inference_url: str,
                 health_url: str,
                 tcp_limit: int = TCP_LIMIT,
                 timeout_limit: int = TIMEOUT_LIMIT,
                 semaphore_limit: int = SEMAPHORE_LIMIT):
        
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
        Validates the presence of required .mp3 files in the audio directory.
    
        This method scans the `self.audio_dir` for .mp3 files and saves the filenames 
        to `self.mp3_filenames`. It compares these filenames to the list of 
        required files extracted from `self.results_path`. If any required files are 
        missing from the directory, a `ValueError` is raised.
        
        Raises:
            ValueError: If any required .mp3 files are missing from the `audio_dir`.
        
        Logs:
            Logs the number of .mp3 files found and any missing files that were 
            expected but not found.
        """
        audio_dir_files = os.listdir(self.audio_dir)
        self.mp3_filenames = [f for f in audio_dir_files if f.endswith('.mp3')]
        logger.info("Found %s .mp3 files.", len(self.mp3_filenames))
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
        logger.info("No missing .mp3 files")

    async def health_check(self, session: aiohttp.ClientSession) -> None:
        """
        Sends an asynchronous GET request to the `health_url` to verify 
        the availability and status of the ASR inference API. It logs the status of 
        the API health check.

        Args:
            session (aiohttp.ClientSession): The aiohttp client session used to make 
                the GET request.

        Raises:
            Exception: If an exception occurs during the request, it is caught and 
                logged as an error.

        Logs:
            Logs a message indicating the success or failure of the health check.
        """
        async with session.get(self.health_url) as resp:
            try:
                if resp.status != 200:
                    logger.info("API Health check failed with status: %s", resp.status)
                else:
                    logger.info("API Health check status ok")
            except Exception as e:
                logger.error("Health check failed: %s", e)

    async def transcribe_single_audio(self,
                                      session: aiohttp.ClientSession,
                                      filename: str) -> dict[str, str]:
        """
        Transcribes a single .mp3 audio file using the ASR inference API.

        This method reads the contents of a .mp3 file from `self.audio_dir`, sends it 
        as a POST request to the ASR API, and returns the transcription and duration 
        of the audio. If the API request fails, an error message is logged, and a 
        dictionary containing the error status is returned.

        Args:
            session (aiohttp.ClientSession): The aiohttp client session used to make 
                the POST request.
            filename (str): The name of the .mp3 file to be transcribed.

        Returns:
            dict[str, str]: A dictionary containing the following keys:
                - 'generated_text' (str): The transcription text from the ASR API.
                - 'duration' (str): The duration of the transcribed audio file.

        Raises:
            Exception: If an unexpected error occurs during file reading or API response parsing.

        Logs:
            Logs an error message if the API request fails.
        """
        audio_filepath = os.path.join(self.audio_dir, filename)
        form = aiohttp.FormData()

        async with aiofiles.open(audio_filepath, 'rb') as f:
            audio_data = await f.read()
            form.add_field('file', audio_data, filename=filename, content_type='audio/mp3')

        async with session.post(self.inference_url, data=form) as resp:
            if resp.status != 200:
                logger.error("Failed to transcribe %s : %s", filename, resp.status)
                return {
                    'generated_text': f'Error: {resp.status}',
                    'duration': f'Error: {resp.status}',
                }

            response = await resp.json()

            return {
                'generated_text': response['transcription'],
                'duration': response['duration'],
            }

    async def transcribe_files_in_dir(self, session: aiohttp.ClientSession) -> List[dict[str, str]]:
        """
        Transcribes all .mp3 files in `self.audio_dir` using concurrency control.

        Method uses an asyncio semaphore to control the concurrency of transcription 
        requests. Each .mp3 file in `self.mp3_filenames` is processed concurrently by 
        calling the `transcribe_single_audio` method. The transcription results for 
        all files are collected and returned as a list of dictionaries.

        Args:
            session (aiohttp.ClientSession): The aiohttp client session used to make 
                API requests for each .mp3 file.

        Returns:
            list[dict[str, str]]: A list of transcription results for each .mp3 file, 
            where each dictionary contains the following keys:
                - 'generated_text' (str): The transcription text from the ASR API.
                - 'duration' (str): The duration of the transcribed audio file.

        Logs:
            Logs progress of the transcription process using `tqdm` and logs the 
            completion of all transcription tasks.
        """
        semaphore = asyncio.Semaphore(self.semaphore_limit)
        tasks = []

        async def transcribe_with_limit(file):
            async with semaphore:
                return await self.transcribe_single_audio(session, filename=file)

        for file in self.mp3_filenames:
            tasks.append(asyncio.ensure_future(transcribe_with_limit(file)))

        results = await tqdm.gather(*tasks,
                                    total=len(tasks),
                                    desc='Transcribing .mp3 files',
                                    file=sys.stderr
                                    )
        logger.info("Completed %s transcription tasks", len(tasks))

        return results

    def write_results(self, results: List[dict[str, str]]) -> None:
        """
        Writes transcription results to a CSV file.

        This method appends the 'generated_text' and 'duration' columns to an existing 
        CSV file specified by `self.results_path`. It updates each row with transcription 
        results from the `results` list, and writes the updated contents to a temporary file. 
        The original file is then replaced with the new file.

        Args:
            results (List[dict[str, str]]): A list of dictionaries where each dictionary 
                contains the transcription result for a file with the following keys:
                - 'generated_text' (str): The transcription text for the audio file.
                - 'duration' (str): The duration of the audio file in seconds.

        Logs:
            Logs the location of the CSV file being written and confirms successful 
            completion of the process.

        Raises:
            FileNotFoundError: If `self.results_path` does not exist or cannot be read.
        """
        parent_dir, filename = os.path.split(self.results_path)
        temp_path = os.path.join(parent_dir, filename + '_temp')

        logger.info('Writing results to: %s', self.results_path)
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
        This method serves as the main entry point for the transcription workflow. 
        It establishes an aiohttp client session with specified TCP and timeout 
        limits. The method first performs a health check on the ASR API. If the 
        health check is successful, it transcribes all audio files in the directory 
        using concurrency control and writes the results to a CSV file.

        Args:
            None

        Returns:
            None

        Logs:
            Logs the status of the health check, the completion of transcription tasks, 
            and the successful writing of transcription results.
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
    logger.info('Program Duration: %.2f seconds', elapsed_time)
