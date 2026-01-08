import os

def read_file(path: str) -> str:
    """
    Reads the content of a file.

    Args:
        path (str): The path to the file to read.

    Returns:
        str: The content of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there is an error reading the file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Error reading file {path}: {e}")

def write_file(path: str, content: str) -> None:
    """
    Writes content to a file.

    Args:
        path (str): The path to the file to write to.
        content (str): The content to write.

    Raises:
        IOError: If there is an error writing to the file.
    """
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        raise IOError(f"Error writing to file {path}: {e}")
