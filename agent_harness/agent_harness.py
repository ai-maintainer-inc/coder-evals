from pathlib import Path
import time
import os
import aim_platform_sdk
from aim_platform_sdk.api import default_api
from aim_platform_sdk.models.user import User
from aim_platform_sdk.models.create_user_request import CreateUserRequest
from aim_platform_sdk.models.errors_response import ErrorsResponse
from aim_platform_sdk import models
from agent_harness.api_comms import (
    api_register_agent,
    handle_bids,
    upload_artifact,
    get_agents,
)

from typing import List, Optional, Union, Tuple
from datetime import datetime
from aim_platform_sdk.models.errors_response import ErrorsResponse
from pathlib import Path
from dataclasses import dataclass


class PythonClientUser:
    """
    This is a class that represents a user of the Python Client and allows connection with the API and git host.
    It has prod default values and allows easy authentication and user creation to our API.
    """

    def __init__(
        self, username: str, password: str, email: str, api_host: str, git_host: str
    ):
        self.username = username
        self.password = password
        self.git_host = git_host
        self.email = email
        self.cfg = aim_platform_sdk.Configuration(
            host=api_host,
            username=self.username,
            password=self.password,
        )
        self.api = aim_platform_sdk.ApiClient(self.cfg)
        self.instance = default_api.DefaultApi(self.api)


def _get_client():
    """
    This is a function that returns a PythonClientUser object with the default values.
    It also fetches the values from the environment variables and raises errors if any of them are not set.
    """
    username = os.getenv("AIM_USERNAME", None)
    password = os.getenv("AIM_PASSWORD", None)
    email = os.getenv("AIM_EMAIL", None)
    host = os.getenv("AIM_API_HOST", "https://platform.ai-maintainer.com/api/v1")
    git_host = os.getenv("AIM_GIT_HOST", "https://git.ai-maintainer.com")
    if not username:
        raise ValueError("AIM_USERNAME is not set.")
    if not password:
        raise ValueError("AIM_PASSWORD is not set.")
    if not email:
        raise ValueError("AIM_EMAIL is not set.")

    return PythonClientUser(username, password, email, host, git_host)


def _register_user() -> PythonClientUser:
    """
    Allows for the creation of a new user who wants to submit agents for benchmarking.

    Args:
        username (str): The username of the user.
        password (str): The password for the user.

    Returns:
        None
    """
    client = _get_client()

    # create user. expect 201 or 409
    req = models.CreateUserRequest(
        userName=client.username, password=client.password, email=client.email
    )
    try:
        response = client.instance.create_user(req)
        assert response.response.status == 201
        return client
    except aim_platform_sdk.exceptions.ApiException as e:
        assert e.status == 409


def maybe_register_user():
    """Get or make a user."""
    client = _register_user()
    if not client:
        client = _get_client()
    return client


def maybe_create_agent(agent_name: str) -> str:
    """
    This function allows for the creation of a new agent, if the agent with that name doesn't already exist for this user.
    If the agent already exists for your user we just fetch it and return the agent_id.
    Either way you get the correct associated agent_id.

    Args:
        username (str): The username of the user.

    Returns:
        str: agent_id
    """
    agents = _fetch_users_agents()
    agent_id = None
    for agent in agents:
        if agent["agentName"] == agent_name:
            agent_id = agent["agentId"]
            break

    if not agent_id:
        agent_id = _register_agent(agent_name)
    return agent_id


def _fetch_users_agents() -> list:
    """
    Fetches all agents for a given user.

    Args:
        username (str): The username of the user.
        password (str): The password for the user.

    Returns:
        list: A list of agents.
    """
    client = _get_client()
    agents = get_agents(client)
    return agents


def _register_agent(agent_name: str) -> str:
    """
    Allows for the creation of a new agent.

    Args:
        username (str): The username of the user.
        password (str): The password for the user.
        agent_name (str): The name of the agent being registered.
        code_path (str): The path to the agent's code.

    Returns:
        str: agent_id
    """
    client = _get_client()
    agents = get_agents(client)
    for agent in agents:
        if agent["agentName"] == agent_name:
            if agent["userName"] == client.username:
                raise ValueError("User already has an agent with this name.")
            else:
                raise PermissionError(
                    f"Agent name {agent_name} is already taken by another user."
                )
    return api_register_agent(client, agent_name)


def get_benchmark_ids(
    benchmark_id: Optional[str] = None,
    author_id: Optional[str] = None,
    author_name: Optional[str] = None,
    title_search: Optional[str] = None,
    difficulty_above: Optional[float] = None,
    difficulty_below: Optional[float] = None,
    page_size: Optional[int] = None,
    page: Optional[int] = None,
    before: Optional[datetime] = None,
    after: Optional[datetime] = None,
    order_by: Optional[str] = None,
    order: Optional[str] = None,
) -> Union[List[str], ErrorsResponse]:
    """
    Get all benchmark tasks from the API, allowing for various query parameters.
    Returns a list of benchmark IDs.

    Args:
        client (ApiClient): The API client instance.
        benchmark_id (Optional[str]): The ID of the benchmark.
        author_id (Optional[str]): The ID of the author.
        author_name (Optional[str]): The name of the author.
        title_search (Optional[str]): Text to search in the title.
        difficulty_above (Optional[float]): Minimum difficulty.
        difficulty_below (Optional[float]): Maximum difficulty.
        page_size (Optional[int]): Number of items per page.
        page (Optional[int]): Page number.
        before (Optional[datetime]): Created before this date-time.
        after (Optional[datetime]): Created after this date-time.
        order_by (Optional[str]): Order by field.
        order (Optional[str]): Order direction.

    Returns:
        Union[List[str], ErrorsResponse]: List of benchmark IDs or ErrorsResponse.
    """
    client = _get_client()

    try:
        api_response = client.instance.get_benchmarks(
            benchmark_id=benchmark_id,
            author_id=author_id,
            author_name=author_name,
            title_search=title_search,
            difficulty_above=difficulty_above,
            difficulty_below=difficulty_below,
            page_size=page_size,
            page=page,
            before=before,
            after=after,
            order_by=order_by,
            order=order,
        )
        print(api_response)
        benchmarks = api_response.benchmarks
        benchmark_ids = [
            benchmark.get("benchmarkId")
            for benchmark in benchmarks
            if "benchmarkId" in benchmark
        ]

        return benchmark_ids

    except aim_platform_sdk.ApiException as e:
        print(f"Exception when calling DefaultApi->get_benchmarks: {e}")
        return ErrorsResponse(errors=[{"message": str(e)}])


@dataclass
class StartBenchmarkResult:
    fork: str
    bid_id: str
    ticket: dict
    cloned_path: Path


def start_benchmark(
    id: int, code_path: Path, agent_id: str = None
) -> StartBenchmarkResult:
    """
    Starts the process of running a benchmark with the given id. When this returns, the agent can start working on the code.

    Args:
        id (int): The ID of the benchmark.
        code_path (Path): The path where code can be dumped into the workspace for the agent to start work.
        agent_id (str): The ID of the agent.

    Returns:
        None
    """
    client = _get_client()
    if not agent_id:
        agent_name = os.getenv("AIM_AGENT_NAME", None)
        if not agent_name:
            raise ValueError(
                "AIM_AGENT_NAME is not set and no agent_id was passed to start_benchmark."
            )
        agent_id = maybe_create_agent(agent_name)

    req = models.CreateBenchmarkTicketRequest(
        agentId=agent_id,
        benchmarkId=id,
    )
    response = client.instance.create_benchmark_ticket(req)
    while True:
        # poll for tickets assigned to this user
        response = client.instance.get_agent_tickets(
            agent_id=agent_id,
        )
        tickets = list(response["tickets"])
        if len(tickets) == 0:
            print("No tickets found. Sleeping.")
            time.sleep(2)
            continue
        ticket_id = tickets[0]["ticketId"]

        # create bid
        req = models.CreateBidRequest(
            agentId=agent_id,
            ticketId=ticket_id,
            rate=0.0,
        )
        response = client.instance.create_bid(req)
        while True:
            # wait for the bids to be accepted.
            fork, bid_id, ticket, cloned_path = handle_bids(client, agent_id, code_path)
            if fork:
                return StartBenchmarkResult(fork, bid_id, ticket, cloned_path)
            time.sleep(0.5)


def ask_question(ticket_id: int, question: str) -> None:
    """
    Allows the agent to ask a clarifying question before starting work on a ticket.

    Args:
        ticket_id (int): The ID of the ticket.
        question (str): The question being asked.

    Returns:
        None
    """
    return "No"


def submit_artifact(start_benchmark_result: StartBenchmarkResult) -> Tuple[str, str]:
    """
    Called when the agent is ready to submit the artifact. This will cause the code to be pushed to our git repo.

    Args:
        workspace (Path): The path to the workspace containing the artifact.

    Returns:
        None
    """
    response = upload_artifact(
        _get_client(),
        start_benchmark_result.fork,
        start_benchmark_result.ticket["code"]["repo"],
        start_benchmark_result.bid_id,
        start_benchmark_result.cloned_path,
    )
    benchmark_artifact_id = response.artifact_id
    return _get_artifact_status(benchmark_artifact_id)


def _get_artifact_status(benchmark_artifact_id: str) -> Tuple[str, str]:
    """
    This assumes your agent has already submitted an artifact and is waiting for it to be evaluated.
    This polls the API for the status of the artifact and returns the status and logs after evaluation has finished.

    Args:
        benchmark_artifact_id (str): The ID of the artifact.

    Returns:
        Tuple[str, str]: The status of the artifact and the logs.
    """
    client = _get_client()
    response = client.instance.get_agents()
    agents = list(response.agents)
    agent_id = agents[0]["agentId"]

    # poll for benchmark artifact status

    status = None
    for i in range(12):
        response = client.instance.get_agent_artifacts(
            agent_id=agent_id, artifact_id=benchmark_artifact_id
        )
        artifacts = list(response.artifacts)
        if len(artifacts) == 0:
            raise ValueError("No artifacts were created.")
        elif artifacts[0]["status"] == "pending":
            print("Waiting for evaluator. Sleeping for 5 seconds")
            time.sleep(5)
            continue

        status = artifacts[0]["status"]
        break

    if not status:
        raise ValueError("Failed to get benchmark artifact status")
    logs = "Sorry, logs aren't available in this version of the Agent Harness.\n\nThey will be available in an upcoming version."

    return status, logs
