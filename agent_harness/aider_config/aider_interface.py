import json
import shutil
import os
import glob
import subprocess
from pathlib import Path
import subprocess
from aider.io import InputOutput
from aider.coders import Coder
from aider.models import Model
from aider.dump import dump


def register_agent(code_path: Path, aider_path: Path):
    """
    This will write a JSON file locally that stores
    1. where the code mount points are.
    2. What the state of the agent is.
    3. What ticket is being worked on (id).
    """
    agent_info = {
        "local_mount_point": str(code_path),
        "state": "idle",
        "ticket_id": None,
        "aider_path": str(aider_path),
    }

    with open("agent.json", "w") as file:
        json.dump(agent_info, file)


def copy_code_to_agent(git_url: str):
    """
    Does a git clone from our go git repo and copies it locally into the mount point of the agent.
    """
    pass


import time


def get_terminal_output(session):
    output = []
    while True:
        line = session.stdout.readline().decode().strip()
        if line == "":
            time.sleep(30)
            line = session.stdout.readline().decode().strip()
            if line == "":
                break
        if line:
            output.append(line)
    return output


def _run_aider_command(command, session):
    # Run the given aider command in the terminal session
    session.stdin.write(f"{command}\n\n\n".encode())
    session.stdin.flush()
    output = get_terminal_output(session)
    return output


def _get_python_files(code_path, aider_path):
    # Get all Python files in the code_path directory
    python_files = glob.glob(f"{code_path}/**/*.py", recursive=True)
    # Make the file paths relative to the code_path
    python_files = [os.path.relpath(file, aider_path) for file in python_files]
    return python_files


def start_terminal_session(input_history_file_path, chat_history_file_path):
    # Start a new terminal session
    session = subprocess.Popen(
        ["/bin/bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )
    # Run the aider command in the new terminal session with selected options
    command = (
        f"aider --yes --no-pretty --verbose --no-auto-commits"
        f" --input-history-file={input_history_file_path}"
        f" --chat-history-file={chat_history_file_path}"
        "\n\n"
    )
    session.stdin.write(command.encode())
    session.stdin.flush()
    return session


def start_agent_task(task_text: str):
    with open("agent.json", "r") as file:
        agent_info = json.load(file)

    local_mount_point = agent_info["local_mount_point"]
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key is None:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Start a new terminal session
    session = start_terminal_session("input_history.txt", "chat_history.txt")

    # Get the terminal output after starting a new session
    initial_output = get_terminal_output(session)
    print("\n".join(initial_output))

    # Get all Python files in the local mount point
    python_files = _get_python_files(local_mount_point, agent_info["aider_path"])

    # Prepare a list of commands to add all Python files at once
    files_to_add = " ".join(python_files)
    add_command = f"/add {files_to_add}"
    add_output = _run_aider_command(add_command, session)
    print("\n".join(add_output))

    # Run aider-chat's /start command
    start_output = _run_aider_command(f"{task_text}", session)
    print("\n".join(start_output))
