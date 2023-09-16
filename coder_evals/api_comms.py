"""
Main module.
This module will spin up an agent harness, it will register that agent.
Then it will track via JSON, which phase in the benchmarking lifecycle the agent is in.

It will then go through the API steps 1 by 1.



"""
import aim_platform_sdk
from aim_platform_sdk import models
from aim_platform_sdk.apis.tags import default_api
from pathlib import Path
import glob

# update this import to use your interface here!
# from agent_harness.aider_config.aider_interface import register_agent, start_agent_task
from aim_git_util.git_util import GitRepo, create_url


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


def get_agents(client):
    """
    Get all agents.

    Parameters:
    - username (str): The username for authentication.
    - password (str): The password for authentication.
    - host (str): The base URL for the API. Defaults to https://platform.ai-maintainer.com/api/v1.

    Returns:
    - list: A list of agents.
    """

    # Get all agents
    response = client.instance.get_agents()
    agents = response.body["agents"]
    return agents


def api_register_agent(user, agent_name):
    """
    Register a new agent using the provided username, password, and agent_data.

    Parameters:
    - username (str): The username for authentication.
    - password (str): The password for authentication.
    - agent_data (dict): The data for the agent to be registered. Should adhere to the Agent model's structure.
    - host (str): The base URL for the API. Defaults to https://platform.ai-maintainer.com/api/v1.

    Returns:
    - dict: The created agent's data or error information.
    """

    req = models.CreateAgentRequest(
        agentName=agent_name,
        webhookSecret="",
        webhookUrl="",
    )

    response = user.instance.create_agent(req)
    agent_id = response.body["agentId"]
    return agent_id


def check_if_agent_exists(user, agent_name):
    """
    Check if an agent exists using the provided username, password, and agent_name.

    Parameters:


    Returns:
    - bool: True if the agent exists, False otherwise.
    """

    # Get all agents
    response = user.instance.get_agents()
    agents = response.body["agents"]
    for agent in agents:
        if agent["agentName"] == agent_name.lower():
            return agent["agentId"]
    return False


def check_for_ticket(client, agent_id):
    response = client.instance.get_agent_tickets(
        query_params={
            "agentId": agent_id,
        }
    )
    tickets = list(response.body["tickets"])
    ticket_id = tickets[0]["ticketId"]

    # create bid
    req = models.CreateBidRequest(
        agentId=agent_id,
        ticketId=ticket_id,
        rate=0.0,
    )
    response = client.instance.create_bid(req)


def handle_bids(client, agent_id, code_path):
    # get agent bids
    response = client.instance.get_agent_bids(
        query_params={
            "agentId": agent_id,
            "status": "pending",
        }
    )
    bids = list(response.body["bids"])
    if len(bids) == 0:
        return None, None, None
    bid_id = bids[0]["bidId"]
    ticket_id = bids[0]["ticketId"]
    response = client.instance.get_agent_tickets(
        query_params={
            "agentId": agent_id,
        }
    )
    tickets = list(response.body["tickets"])
    ticket = None
    # find the ticket with the same ticketId as the bid
    for ticket in tickets:
        if ticket["ticketId"] == ticket_id:
            ticket = ticket
            break
    if ticket is None:
        return None, None, None
    # get the code from the ticket
    code = ticket["code"]
    repo = code["repo"]

    # fork the code
    req = models.CreateRepositoryRequest(
        repositoryName=repo,
        isPublic=False,
    )
    try:
        response = client.instance.create_repository(req)
        assert response.response.status == 201
    except aim_platform_sdk.ApiException as e:
        assert e.status == 409

    url = create_url(client.git_host, code["owner"], code["repo"])
    gitrepo = GitRepo(url, client.username, client.password)
    fork_url = create_url(client.git_host, client.username, repo)
    gitrepo.fork(fork_url, force=True)
    fork = GitRepo(fork_url, client.username, client.password)
    fork.clone(code_path + "/" + repo)
    return fork, bid_id, ticket, code_path + "/" + repo


def upload_artifact(
    client: PythonClientUser,
    fork: GitRepo,
    repo: str,
    bid_id: str,
    path: Path,
):
    # list all files in repo path:
    files = glob.glob(path + "/**/*", recursive=True)
    fork.add(path, all=True)
    if fork.has_changes(path):
        fork.commit(path, "add README.md")
        fork.push(path)

    # create artifact
    req = models.CreateArtifactRequest(
        bidId=bid_id,
        code=models.Code(
            owner=client.username,
            repo=repo,
            branch="",
            commit="",
        ),
        draft=False,
    )
    try:
        response = client.instance.create_artifact(req)
        assert response.response.status == 201
    except aim_platform_sdk.ApiException as e:
        print(f"Error creating artifact: {e}")
        raise e

    # done to make sure we don't loop forever
    return response
