import threading
import subprocess
import logging
from . import paths

def logging_handler(line: str, cpp_binary_name: str):

    line = line.removesuffix("\n")

    if line.startswith("INFO: "):
        logging.info(f"{cpp_binary_name}: {line.replace('INFO: ', '')}")
    
    elif line.startswith("DEBUG: "):
        logging.debug(f"{cpp_binary_name}: {line.replace('DEBUG: ', '')}")

    elif line.startswith("WARNING: "):
        logging.warning(f"{cpp_binary_name}: {line.replace('WARNING: ', '')}")
    
    elif line.startswith("ERROR: "):
        logging.error(f"{cpp_binary_name}: {line.replace('ERROR: ', '')}")
    
    else:
        logging.debug(f"{cpp_binary_name}: {line}")

def _cpp_worker_thread(cpp_binary_name: str, stdin: str, cpp_worker_args: list):
    logging.debug(f"Invoking {cpp_binary_name}")
    process = subprocess.Popen(
        args=[str(paths.CPP_UTILS_PATH / cpp_binary_name), *cpp_worker_args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8"
    )
    logging.debug(f"{cpp_binary_name} invoked successfully")

    process.stdin.write(stdin)
    process.stdin.close()

    for line in process.stdout:
        logging_handler(line, cpp_binary_name)
    
    return_code = process.wait()
    logging.debug(f"{cpp_binary_name} exited with exit code: {return_code}")

def cpp_worker(cpp_binary_name: str, stdin: str, cpp_worker_args: list):
    logging.debug(f"Spawning {cpp_binary_name} background worker thread")

    cpp_binary_path = paths.CPP_UTILS_PATH / cpp_binary_name
    if not cpp_binary_path.exists():
        logging.error(f"C++ binary {cpp_binary_name} not found.")
        raise FileExistsError(f"Native binary missing at: {cpp_binary_path}")
    
    cpp_worker_thread = threading.Thread(
        target=_cpp_worker_thread,
        args=(cpp_binary_name, stdin, cpp_worker_args),
        daemon=True
    )
    cpp_worker_thread.start()
    logging.debug(f"{cpp_binary_name} successfully handed off to background worker thread.")