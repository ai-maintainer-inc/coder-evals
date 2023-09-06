import json
import os
import glob
from pathlib import Path
from aider.io import InputOutput
from aider.coders import Coder
from aider.models import Model
from aider.dump import dump
import openai


def register_agent(code_path: Path, aider_path: Path, agentName: str) -> Path:
    """
    This will write a JSON file locally that stores
    1. where the code mount points are.
    2. What the state of the agent is.
    3. What ticket is being worked on (id).
    """
    # if there is no agent.json file, create one, otherwise return the path to the existing one
    filename = f"{agentName}.json"
    if not Path(filename).exists():
        agent_info = {
            "agentName": agentName,
            "local_mount_point": str(code_path),
            "state": 0,
            "ticket_id": None,
            "aider_path": str(aider_path),
        }

        with open(filename, "w") as file:
            json.dump(agent_info, file)

    # return the path of the agent.json
    return Path(filename).absolute()


def _get_files_with_exts(code_path, aider_path, exts):
    # Get all Python files in the code_path directory
    all_files = []
    for ext in exts:
        all_files.extend(glob.glob(f"{code_path}/**/*.{ext}", recursive=True))
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
    coder.run(with_message=task_text)
