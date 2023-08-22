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
import openai


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


def _get_python_files(code_path, aider_path):
    # Get all Python files in the code_path directory
    python_files = glob.glob(f"{code_path}/**/*.py", recursive=True)
    # Make the file paths relative to the code_path
    python_files = [os.path.relpath(file, aider_path) for file in python_files]
    return python_files


def start_agent_task(task_text: str):
    with open("agent.json", "r") as file:
        agent_info = json.load(file)

    local_mount_point = agent_info["local_mount_point"]
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key is None:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Start a new terminal session
    io = InputOutput(
        pretty=True,
        yes=False,
        chat_history_file="chat_history.txt",
    )

    main_model = Model("gpt-4")
    edit_format = main_model.edit_format

    dump(main_model)
    dump(edit_format)
    fnames = _get_python_files(local_mount_point, agent_info["aider_path"])
    show_fnames = ",".join(map(str, fnames))
    print("fnames:", show_fnames)

    openai.api_key = os.environ["OPENAI_API_KEY"]

    coder = Coder.create(
        main_model,
        edit_format,
        io,
        fnames=fnames,
        use_git=False,
        stream=False,
        pretty=False,
        verbose=True,
    )

    timeouts = 0
    coder.run(with_message=task_text)
