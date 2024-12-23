#!/bin/bash

# NOTE: Make sure you are at the root folder ./asr-submission before executing any of the selection here
# Root Directory

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo $ROOT_DIR

# Display the menu
display_menu() {
  echo "1. Create environment and install requirements"
  echo "2. Run asr-api on docker"
  echo "3. View cv-transcriptions search engine"
  echo "4. Exit"
  echo -n "Enter one of the following numbers: "
}

create_env() {
    conda create --name asr_rosamund python=3.11.11
    conda activate asr_rosamund
    pip install -r requirements.txt
}

run_asr_api_docker() {
    docker build -f ./asr/Dockerfile -t asr-api .
    docker run -p 8001:8001 -d --name transcribe asr-api
    echo "asr-api docker is running in background."
    echo "To transcribe .mp3 files, run $ python cv-decode.py from asr/ folder." 
    echo "IMPT NOTE: Ensure you have the mp3 files in 'cv-valid-dev' folder "
    read -p "Would you like to stop the Docker container now? (Y/N): " stop_choice
    if [[ "$stop_choice" =~ ^[Yy]$ ]]; then
        docker stop transcribe && docker rm transcribe
        echo "Docker container 'transcribe' has been stopped and removed."
    else
        echo "Docker container 'transcribe' is still running."
    fi
}

view_search_ui() {
    cd elastic-backend
    docker-compose up -d
    cd ../search-ui/app-search-reference-ui-react-master/src    
    yarn start
}

# Main script loop
while true; do
  display_menu

  read -r choice

  case $choice in
    1)
      create_env;;
    2)
      run_asr_api_docker;;
    3)
      view_search_ui;;
    4)
      echo "Exiting. Goodbye!"
      exit 0 ;;
    *)
      echo "Invalid option. Please select a valid number (1-4)." ;;
  esac
  echo ""
done
