import json
import shutil
import os
import glob
import subprocess
from pathlib import Path
import subprocess


def register_agent(code_path: Path):
    """
    This will write a JSON file locally that stores
    1. where the code mount points are.
    2. What the state of the agent is.
    3. What ticket is being worked on (id).
    """
    agent_info = {
        "local_mount_point": code_path,
        "state": "idle",
        "ticket_id": None,
    }

    with open("agent.json", "w") as file:
        json.dump(agent_info, file)


def copy_code_to_agent(git_url: str):
    """
    Does a git clone from our go git repo and copies it locally into the mount point of the agent.
    """
    pass


def _run_aider_command(command, agent_info):
    # Run the given aider command
    response = subprocess.run(
        f"{command}",
        shell=True,
        cwd=str(agent_info["local_mount_point"]),
        capture_output=True,
    )
    return response.stdout.decode().strip()


def _get_python_files(code_path):
    # Get all Python files in the code_path directory
    python_files = glob.glob(f"{code_path}/**/*.py", recursive=True)
    return python_files


def start_terminal_session():
    # Start a new terminal session
    session = subprocess.Popen(["/bin/bash"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    # Run the aider command in the new terminal session
    session.stdin.write(b"aider\n")
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
    session = start_terminal_session()

    # Get all Python files in the local mount point
    python_files = _get_python_files(local_mount_point)

    # Prepare a list of commands to add all Python files at once
    files_to_add = " ".join(python_files)
    add_command = f"/add {files_to_add}"
    _run_aider_command(add_command, agent_info, session)

    # Run aider-chat's /start command
    _run_aider_command(f"{task_text}", agent_info, session)

    return _run_aider_command("/diff", agent_info, session)
