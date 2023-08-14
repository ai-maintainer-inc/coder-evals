import json
import docker
import shutil
import os
import glob
from pathlib import Path


def register_agent(code_path: Path):
    """
    This will write a JSON file locally that stores
    1. where the code mount points are.
    2. What the state of the agent is.
    3. What ticket is being worked on (id).
    """
    agent_info = {
        "local_mount_point": code_path,
        "agent_mount_point": "/code",
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


def _run_aider_command(container, command):
    # Run the given aider command inside the specified container
    response = container.exec_run(f"sh -c 'aider-chat {command}'", workdir="/code")
    return response.output.decode().strip()


def _get_python_files(mount_point, code_path):
    # Get all Python files in the code_path directory
    python_files = glob.glob(f"{code_path}/**/*.py", recursive=True)

    # Replace the base path with the mount point
    python_files_in_container = [
        file_path.replace(code_path, mount_point) for file_path in python_files
    ]

    return python_files_in_container


def start_agent_task(task_text: str):
    with open("agent.json", "r") as file:
        agent_info = json.load(file)

    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    # dockerfile_path = current_dir / "aider_config"

    client = docker.from_env()

    # Build the Docker image from the Dockerfile
    image_name = "aider-chat-image"
    client.images.build(path=str(current_dir), tag=image_name)

    local_mount_point = agent_info["local_mount_point"]
    agent_mount_point = agent_info["agent_mount_point"]
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key is None:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Start the Docker container
    container = client.containers.run(
        image_name,
        volumes={local_mount_point: {"bind": agent_mount_point, "mode": "rw"}},
        environment={"OPENAI_API_KEY": openai_api_key},
        detach=True,
    )

    # Get all Python files in the container's mount point
    python_files = _get_python_files(agent_info["agent_mount_point"], local_mount_point)

    # Prepare a list of commands to add all Python files at once
    files_to_add = " ".join(python_files)
    add_command = f"/add {files_to_add}"
    _run_aider_command(container, add_command)

    # Run aider-chat's /start command
    _run_aider_command(container, f"/start {task_text}")

    return _run_aider_command(container, "/diff")
