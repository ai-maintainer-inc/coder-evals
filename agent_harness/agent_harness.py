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


from pathlib import Path
import time


import openapi_client
from openapi_client.apis.tags import default_api
from openapi_client.model.user import User
from openapi_client.model.create_user_request import CreateUserRequest
from openapi_client.model.errors_response import ErrorsResponse
from openapi_client import models
from pprint import pprint
from agent_harness.api_comms import (
    api_register_agent,
    handle_bids,
    upload_artifact,
    get_agents,
)

from typing import List, Optional, Union, Tuple
from datetime import datetime
from openapi_client import ApiClient
from openapi_client.model.benchmarks_response import BenchmarksResponse
from openapi_client.model.errors_response import ErrorsResponse
from pathlib import Path


class PythonClientUser:
    def __init__(self, username: str, password: str, api_host: str, git_host: str):
        self.username = username
        self.password = password
        self.git_host = git_host
        self.cfg = openapi_client.Configuration(
            host=api_host,
            username=self.username,
            password=self.password,
        )
        self.api = openapi_client.ApiClient(self.cfg)
        self.instance = default_api.DefaultApi(self.api)


def register_user(
    username: str,
    password: str,
    email: str,
    api_host: str = "https://api-ai-maintainer-7ovqsdkn2q-uc.a.run.app/api/v1",
    git_host: str = "https://git-server-7ovqsdkn2q-uc.a.run.app",
) -> PythonClientUser:
    """
    Allows for the creation of a new user who wants to submit agents for benchmarking.

    Args:
        username (str): The username of the user.
        password (str): The password for the user.

    Returns:
        None
    """
    client = PythonClientUser(username, password, api_host, git_host)

    # create user. expect 201 or 409
    req = models.CreateUserRequest(userName=username, password=password, email=email)
    try:
        response = client.instance.create_user(req)
        assert response.response.status == 201
        return client
    except openapi_client.exceptions.ApiException as e:
        assert e.status == 409


def fetch_users_agents(client) -> list:
    """
    Fetches all agents for a given user.

    Args:
        username (str): The username of the user.
        password (str): The password for the user.

    Returns:
        list: A list of agents.
    """
    agents = get_agents(client)
    return agents


def register_agent(client, agent_name: str) -> str:
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
    agents = get_agents(client)
    for agent in agents:
        print("agent:", agent)
        if agent["agentName"] == agent_name:
            if agent["userName"] == client.username:
                raise ValueError("User already has an agent with this name.")
            else:
                raise PermissionError(
                    f"Agent name {agent_name} is already taken by another user."
                )
    return api_register_agent(client, agent_name)


def get_benchmarks(
    client: ApiClient,
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
    query_params = {
        "benchmarkId": benchmark_id,
        "authorId": author_id,
        "authorName": author_name,
        "titleSearch": title_search,
        "difficultyAbove": difficulty_above,
        "difficultyBelow": difficulty_below,
        "pageSize": page_size,
        "page": page,
        "before": before,
        "after": after,
        "orderBy": order_by,
        "order": order,
    }

    try:
        api_response = client.instance.get_benchmarks(query_params=query_params)

        # Extracting benchmark IDs from the response
        print("api_response.body:", api_response.body)
        benchmarks = api_response.body.get("benchmarks", [])
        benchmark_ids = [
            benchmark.get("benchmarkId")
            for benchmark in benchmarks
            if "benchmarkId" in benchmark
        ]

        return benchmark_ids

    except openapi_client.ApiException as e:
        print(f"Exception when calling DefaultApi->get_benchmarks: {e}")
        return ErrorsResponse(errors=[{"message": str(e)}])


def start_benchmark(client, id: int, code_path: Path, agent_id: str) -> None:
    """
    Starts the process of running a benchmark with the given id. When this returns, the agent can start working on the code.

    Args:
        id (int): The ID of the benchmark.
        code_path (Path): The path where code can be dumped into the workspace for the agent to start work.

    Returns:
        None
    """
    req = models.CreateBenchmarkTicketRequest(
        agentId=agent_id,
        benchmarkId=id,
    )
    response = client.instance.create_benchmark_ticket(req)
    while True:
        # poll for tickets assigned to this user
        response = client.instance.get_agent_tickets(
            query_params={
                "agentId": agent_id,
            }
        )
        tickets = list(response.body["tickets"])
        print("tickets:", tickets)
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
        print("response.body:", response.body)

        while True:
            # wait for the bids to be accepted.
            fork, bid_id, ticket, cloned_path = handle_bids(client, agent_id, code_path)
            print("fork:", fork)
            if fork:
                return fork, bid_id, ticket, cloned_path
            time.sleep(0.5)


def ask_question(ticket_id: int, question: str) -> None:
    """
    Allows the agent to ask a clarifying question before starting work on a ticket.

    Args:
        ticket_id (int): The ID of t    he ticket.
        question (str): The question being asked.

    Returns:
        None
    """
    return "No"


def submit_artifact(client, fork, repo: str, bid_id: str, path: Path) -> None:
    """
    Called when the agent is ready to submit the artifact. This will cause the code to be pushed to our git repo.

    Args:
        workspace (Path): The path to the workspace containing the artifact.

    Returns:
        None
    """
    upload_artifact(client, fork, repo, bid_id, path)
