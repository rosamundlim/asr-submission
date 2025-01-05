
# Deploying Automatic Speech Recognition (ASR) Model to transcribe .mp3 audio files

## 1. Introduction

In this project, I deploy Facebook's wav2vec2-large-90h model (henceforth referred as 'Wav2vec2'), an automatic speech recognition (ASR) model, to transcribe 4,076 .mp3 audio files from the Common Voice Dataset. Note that Wav2vec2 is pretrained and fine-tuned on Librispeech dataset on 16kHz sampled speech audio.

## 2. Main Techstack

Note that for this project, I am using Python 3.11.11

- Basic: Python, CLI, Shell Scripting
- AI/ML Libraries: Transformers, Torch
- Audio: Librosa
- Deployment: FastAPI, Docker, ElasticSearch, Search-UI
- Cloud: AWS EC2, AWS S3
- Testing: PyTest
- Version Control: git version control
- Others: asyncio, aiohttp, aiofiles, pydantic, pyYaml

## 3. Overall Directory Structure
```
.
└── asr-submission/
    ├── asr/
    ├── assets/
    ├── deployment-design/
    ├── elastic-backend/
    ├── node_modules/
    ├── search-ui/
    ├── .gitignore
    ├── essay.pdf
    ├── package-lock.json
    ├── README.md
    ├── requirements.txt
    └── run.sh
```

- NOTE: I store paths and .env variables, secrets in separate files rather than hardcoding them into the main script (security purposes)

## 4. Setup

There is a run.sh file at root level, with the options:

1. Create Environment and Install Requirements:
Sets up a Conda environment and installs Python dependencies.

2. Builds and runs a Docker container for the ASR API.
Offers an option to stop and remove the container.

3. Starts Elasticsearch backend services using Docker Compose.
Launches the search UI with Yarn.
Exit:

4. Safely exits the script.

To execute run.sh, simply cd to the root folder `./asr-submission`, and execute `./run.sh` in your bash terminal or equivalent. 

## 5. asr/ directory

```
asr/
├── __init__.py
├── paths.py
├── utility_functions.py
├── conf/
│   ├── config.yml
│   └── openapi.yml
├── cv-valid-dev
├── logs
├── notebooks/
│   └── inference.ipynb
├── tests/
│   ├── __init__.py
│   └── test_utility_functions.py
├── .dockerignore
├── asr_api.py
├── cv-decode.py
├── cv-valid-dev.csv
└── Dockerfile
```

The above shows the structure of the asr/ directory: 
- `paths.py`: Stores directories and filepaths required for asr/ tasks to ensure modularity avoid hardcoding into  scripts
- `utility_functions.py`: Defines helper functions for asr transcription tasks
- `conf/`: Folder contains config files. `config.yml` contains the settings/params for asr transcription tasks; `openapi.yml` defines the API's structure, endpoints, and operations in a standardized format for documentation, testing, and client generation.
- `cv-valid-dev/`: Folder that contains 4,076 .mp3 audio files that will be used for transcription (.gitignore due to size)
- `logs`: Contains logs of running `cv-decode.py` script. folders in logs represent `yyyy-mm-dd` (date where script was run) and individual files are named `hh-mm-ss` (time where script started running). This convention will ensure the logs are organized and makes it easier for user to find their logs. 
- `notebooks/`: Folder contains `inference.ipynb`, which reproduces the inference pipeline tutorial in Wav2Vec2's Hugging Face card. 
- `tests/`: Folder contains `test_utility_functions.py`, which contains tests (PyTest Framework) for functions used in `asr_api.py` and `cv-decode.py`.
- `.dockerignore` : Folders/files that Dockerfile should ignore when containerizing `asr_api.py`.
- `asr_api.py`: FastAPI deployment of the inference pipeline
- `cv-decode.py`: Script that calls FastAPI to transcribe all 4,076 .mp3 files in `cv-valid-dev/`.
- `Dockerfile`: Docker instructions to containerize `asr_api.py`.

### 5.1 asr_api.py

This is the app module that serves the Wav2Vec2 Inference Pipeline as a FastAPI app. 
This script defines a FastAPI app for ASR tasks, loading a Wav2Vec model at startup. It includes a health check endpoint and an ASR endpoint that processes .mp3 files to return transcriptions and durations, using utility functions for audio processing and error handling.

#### 5.1.1 Containerizing asr_api.py

i. To build a docker image, run the following in terminal from root ./asr-submission directory

```docker build -f ./asr/Dockerfile -t asr-api .``` 

ii. To run docker container, run the following commands in terminal

```docker run -p 8001:8001 --name <container name> <img name>```

#### 5.1.2 UploadFile 

Data Privacy issues are of concern whenever users upload something onto the web. The `UploadFile` class from
FastAPI is built on [starlette](https://www.starlette.io/requests/). It uses [SpooledTemporaryFile](https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile) under the hood. Data is spooled in memory until the file size exceeds max_size, at which point the contents are written to disk and operation proceeds as with [TemporaryFile()](https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryFile). This means that files written to disk are managed securely and are automatically destroyed when closed, either explicitly by the application or implicitly through garbage collection. This behavior ensures that temporary files do not persist longer than necessary, reducing the risk of inadvertent data retention.


### 5.2 cv-decode.py

This is a API microservice which transcribes .mp3 files. To run this select option 2 when executing run.sh. Ensure you have requirements installed beforehand (option 1 in run.sh)

The script validates audio files, checks API health, and transcribes files concurrently 
using aiohttp and asyncio, adhering to specified TCP and timeout limits. Transcription results, 
including text and duration, are written to a CSV file.

#### 5.2.1 error logs

| Error      | Fix |
| ----------- | ----------- |
| Connection timeout when script ran for the first time as no limit set on no. of concurrent jobs | set   aiohttp_tcp_connectors=100; aiohttp_timeout=600; semaphore_limit=50, to limit concurrent jobs|

## 6. elastic-backend/ directory

Now that we have the transcriptions of the 4,076 .mp3 files in `cv-valid-dev.csv`, we will next try to create a search engine to serve the 4,076 transcriptions. 
The elastic-backend/ directory serves as the backend code for the search engine. 

```
elastic-backend/
├── eb_utils/
│   ├── __init__.py
│   ├── paths.py
│   └── utility_functions.py
├── .env (in .gitignore)
├── .env.example
├── ca.crt (in .gitignore)
├── config.yml
├── cv-index.py
├── docker-compose.yml
├── eda.ipynb
└── elasticsearch.yml
```

- `eb_utils/` : contains scripts for utility functions and defined paths used in `cv-index.py`
- `.env` : git ignored. see `.env.example` for a sample of what to include for .env
- `.env.example`: sample for `.env` which is git ignored.
- `ca.crt`: a ca certificate. copied from container. It allows the client to verify ElasticSearch's server authenticity. 
- `config.yml`: contains the configurations for the backend, including column mappings and endpoint url to be used in indexing in ElasticSearch. 
- `docker-compose.yml`: defines the two-node ElasticSearch cluster. Adapted from ElasticSearch's [github repository](https://github.com/elastic/elasticsearch/blob/main/docs/reference/setup/install/docker/docker-compose.yml)
- `eda.ipynb`: notebook to explore the data in `cv-valid-dev.csv`.
- `elastcsearch.yml`: allows cluster to listen on all network interfaces (0.0.0.0), and enables CORS (Cross-Origin Resource Sharing) with unrestricted origins (*), specific headers, and HTTP methods to allow external applications to interact with the cluster. `elasticsearch.yml` is mounted to the ElasticSearch container (example, line 65 in `docker-compose.yml`)

### 6.1 Run 2-node ElasticSearch Cluster with docker compose

i. cd to elastic-backend/ directory

ii. Configure and start the cluster (Ensure you have docker running)

`-d` flag runs in dontainer in background

```
$ docker-compose up -d
```

iii. Run cv-index.py

Ensure you are in elastic-backend/ directory

```
$ python cv-index.py
```

You should expect to see the following, if you are successfully connected to the cluster: 

```
elastic
2025-01-04 14:59:51,561:INFO:GET https://localhost:9200/ [status:200 duration:0.022s]
{'name': 'es01', 'cluster_name': 'docker-cluster', 'cluster_uuid': 'TtB378WWTFaSh7EsLOYY1g', 'version': {'number': '8.12.0', 'build_flavor': 'default', 'build_type': 'docker', 'build_hash': '1665f706fd9354802c02146c1e6b5c0fbcddfbc9', 'build_date': '2024-01-11T10:05:27.953830042Z', 'build_snapshot': False, 'lucene_version': '9.9.1', 'minimum_wire_compatibility_version': '7.17.0', 'minimum_index_compatibility_version': '7.0.0'}, 'tagline': 'You Know, for Search'}
```

iv. Stop and remove the cluster

```
$ docker-compose down
```
To delete the network, containers, and volumes when you stop the cluster, specify the -v option:
```
$ docker-compose down -v
```
## 7. search-ui/ directory

The frontend for the search engine will be search-ui, ElasticSearch's tool to build search interfaces for data indexed in ElasticSearch database. 

**<u>Note that for this section, I will only highlight _important_ folders/files in the tree structure and ignore the others</u>**. 

```
search-ui/
├── app-search-reference-ui-react-master/
│   ├── build
│   └── src/
│       ├── config/
│       │   ├── config-helper.js
│       │   ├── engine.json (in .gitignore)
│       │   └── engine.json.example 
│       ├── App.js
│       ├── index.js
│       ├── secrets.json (in .gitignore)
│       └── secrets.json.example
├── node_modules/ (in .gitignore)
├── package-lock.json
├── package.json
└── yarn.lock
```

- `app-search-reference-ui-react-master`: This folder can be generated by following elastic's [tutorial](https://www.elastic.co/guide/en/search-ui/current/tutorials-elasticsearch.html) for building Search UI with ElasticSearch. 
    - Within this folder, `src/` Contains source code for implementation of a search UI built using React and Elastic App Search.
    - `config/` stores the settings for connecting Search UI with ElasticSearch. 
    - `secrets.json` stores environment variables. Refer to `config/engine.json.example` and `secrets.json.example` for samples. 
    - Finally `build/` folder contains the production ready version (static assets) of the frontend; created by running `yarn build`. 

- `node_modules`: Directory containing installed dependencies and their sub-dependencies for the project.  
- `package-lock.json`: Auto-generated file ensuring consistent dependency versions across installs.  
- `package.json`: File specifying project metadata, dependencies, and scripts.  
- `yarn.lock`: Lockfile for Yarn, ensuring consistent dependency versions across installs.  

### 7.1 Deployment Design 

The following document contains a simple diagram showing the deployment design of the search engine. 

[text](deployment-design/design.pdf)

### 7.2 Connecting to Elastic Search on AWS

i. Start a AWS EC2 instance with Amazon Linux 2023 AMI (t2.medium) <br>
ii. Install Elasticsearch from archive on Linux following this [tutorial](https://www.elastic.co/guide/en/elasticsearch/reference/current/targz.html).

Additionally, the following error logs shows some of the issues and fixes during the deployment of ELasticSearch over the AWS EC2 Instance. 

| Errors  | Fixes |
| ------------- | ------------- |
| rpm seems to have trouble, exit code 1  | used tar |
| vm.max_map_count too low | changed to 262144  |
| sudo curl --cacert $ES_HOME/config/certs/http_ca.crt -u elastic:$ELASTIC_PASSWORD https://localhost:9200 error: curl: (77) error setting certificate file: /config/certs/http_ca.crt | chmod -R a+r /home/ec2-user/elasticsearch-8.17.0/config/certs
|search-ui yarn start: fatal alert: certificate unknown | ElasticsearchAPIConnector unable to pass in https ca SHA fingerprint even but elasticsearch.yml enables xpack.security.http.ssl.enabled = true. I tried to refactored App.js code based on official documentation to connect to cluster via javascript: https://www.elastic.co/guide/en/elasticsearch/client/javascript-api/current/client-connecting.html, that did not work. My workaround is to : Disable xpack.security.http.ssl.enabled = true to xpack.security.http.ssl.enabled = false in order to run the website with ElasticsearchAPIConnector. Implications: only use http instead of http now. |


### 7.3 Designing the front-end of the search engine

`search-ui/app-search-reference-ui-react-master/src/App.js` holds the layout of the search engine. I followed and adapted code from ElasticSearch's sample in this [tutorial](https://www.elastic.co/guide/en/search-ui/current/tutorials-elasticsearch.html#tutorials-elasticsearch-installing-connector). 
This allows me to include:
- `generated__text`, which is the transcriptions generated from Wav2Vec2 as a searchable field. 
- `age`, `gender`, `accent`, `duration`: as fields that can be filtered to refine the search results. 

Below is a preview: 
![alt text](assets/cv-index-search-engine.png)

### 7.4 Deploying as a static website 

I ran `yarn build` in, generating the `search-ui/app-search-reference-ui-react-master/build/` folder. I uploaded the folder into an Amazon S3 bucket, and enabled static website hosting. 

**_Please Note_**:  Due to costs, I have undeployed the app. However below is a screenshot of its deployment. An example query is also shown by searching "WINE" and checking the "5-10 sec" filter box. 

Expected result: 

![alt text](assets/cv_transcriptions_static_wesbite.png)
