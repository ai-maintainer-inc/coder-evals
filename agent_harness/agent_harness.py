"""
This is a file that has the following implemented.

# allows for the creation of a new user who wants to submit agents for benchmarking
register_user(username, password)

# allows for the creation of a new agent
register_agent(username, password, agent_name, code_path)

# allows for querying of benchmarks so users can easily choose what benchmarks they want to run
get_benchmark_ids(category=[], name=None, version='latest')

# starts the process of running a benchmark with the given id when this returns the agent can start working on the code
start_benchmark(id)

# allows the agent to ask a clarifying question before starting work on a ticket
ask_question(ticket_id, question)

# called when the agent is ready to submit the artifact. This will cause the code to be pushed to our git repo
submit_artifact(workspace: Path)
"""


def register_user(username: str, password: str) -> None:
    """
    Allows for the creation of a new user who wants to submit agents for benchmarking.

    Args:
        username (str): The username of the user.
        password (str): The password for the user.

    Returns:
        None
    """
    pass


def register_agent(
    username: str, password: str, agent_name: str, code_path: str
) -> None:
    """
    Allows for the creation of a new agent.

    Args:
        username (str): The username of the user.
        password (str): The password for the user.
        agent_name (str): The name of the agent being registered.
        code_path (str): The path to the agent's code.

    Returns:
        None
    """
    pass


def get_benchmark_ids(
    category: list = [], name: str = None, version: str = "latest"
) -> list:
    """
    Allows for querying of benchmarks so users can easily choose what benchmarks they want to run.

    Args:
        category (list, optional): The category of benchmarks. Defaults to [].
        name (str, optional): The name of the benchmark. Defaults to None.
        version (str, optional): The version of the benchmark. Defaults to 'latest'.

    Returns:
        list: A list of benchmark IDs.
    """
    pass


def start_benchmark(id: int) -> None:
    """
    Starts the process of running a benchmark with the given id. When this returns, the agent can start working on the code.

    Args:
        id (int): The ID of the benchmark.

    Returns:
        None
    """
    pass


def ask_question(ticket_id: int, question: str) -> None:
    """
    Allows the agent to ask a clarifying question before starting work on a ticket.

    Args:
        ticket_id (int): The ID of the ticket.
        question (str): The question being asked.

    Returns:
        None
    """
    pass


from pathlib import Path


def submit_artifact(workspace: Path) -> None:
    """
    Called when the agent is ready to submit the artifact. This will cause the code to be pushed to our git repo.

    Args:
        workspace (Path): The path to the workspace containing the artifact.

    Returns:
        None
    """
    pass
