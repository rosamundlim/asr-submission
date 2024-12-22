"""Stores utility functions for elastic-backend"""

import yaml

def load_yaml(path: str) -> dict:
    """
    Loads and parses a YAML file from the specified path.

    Args:
        path (str): The path to the YAML file to be loaded.

    Returns:
        dict: The parsed YAML content as a Python dictionary.
              If the content is a list or other type, it will still be returned,
              but the type hint assumes a dictionary for simplicity.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.
        UnicodeDecodeError: If the file cannot be decoded using UTF-8.
    """
    with open(path, 'r', encoding='UTF8') as file:
        yaml_file = yaml.safe_load(file)
        return yaml_file
    
