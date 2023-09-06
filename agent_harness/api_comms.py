"""
Main module.
This module will spin up an agent harness, it will register that agent.
Then it will track via JSON, which phase in the benchmarking lifecycle the agent is in.

It will then go through the API steps 1 by 1.



"""
import openapi_client
from openapi_client.apis.tags import default_api
from openapi_client.model.create_agent_request import CreateAgentRequest
from openapi_client.model.errors_response import ErrorsResponse
from openapi_client import models
from pathlib import Path
import shutil
import glob

# update this import to use your interface here!
# from agent_harness.aider_config.aider_interface import register_agent, start_agent_task
from ai_maintainer_git_util.ai_maintainer_git_util import GitRepo, create_url


# API_HOST = "http://marketplace-api:8080/api/v1"
# GIT_HOST = "http://git-server:8080"
# CLIENT_USERNAME = "test_user1"

# CLIENT_CODE_OWNER = CLIENT_USERNAME
# CLIENT_CODE_REPO = "repo1"
# OPERATOR_USERNAME = "test_user2"
# OPERATOR_PASSWORD = "F@k3awefawefawef"
# OPERATOR_CODE_OWNER = OPERATOR_USERNAME
# OPERATOR_CODE_REPO = "repo2"


def get_agents(client):
    """
    Get all agents.

    Parameters:
    - username (str): The username for authentication.
    - password (str): The password for authentication.
    - host (str): The base URL for the API. Defaults to https://marketplace-api.ai-maintainer.com/v1.

    Returns:
    - list: A list of agents.
    """

    # Get all agents
    response = client.instance.get_agents()
    print(response)
    print(response.body)
    agents = response.body["agents"]
    print(agents)
    return agents


def api_register_agent(user, agent_name):
    """
    Register a new agent using the provided username, password, and agent_data.

    Parameters:
    - username (str): The username for authentication.
    - password (str): The password for authentication.
    - agent_data (dict): The data for the agent to be registered. Should adhere to the Agent model's structure.
    - host (str): The base URL for the API. Defaults to https://marketplace-api.ai-maintainer.com/v1.

    Returns:
    - dict: The created agent's data or error information.
    """

    req = models.CreateAgentRequest(
        agentName=agent_name,
        webhookSecret="",
        webhookUrl="",
    )

    response = user.instance.create_agent(req)
    print("response.body:", response.body)
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
    print("pending bids:", bids)
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
    print("ticket:", ticket)
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
    except openapi_client.ApiException as e:
        assert e.status == 409

    url = create_url(client.git_host, code["owner"], code["repo"])
    gitrepo = GitRepo(url, client.username, client.password)
    fork_url = create_url(client.git_host, client.username, repo)
    gitrepo.fork(fork_url, force=True)
    fork = GitRepo(fork_url, client.username, client.password)
    print("path:", code_path)
    fork.clone(code_path + "/" + repo)
    return fork, bid_id, ticket, code_path + "/" + repo


def upload_artifact(client, fork: GitRepo, repo: str, bid_id: str, path: Path):
    # list all files in repo path:
    files = glob.glob(path + "/**/*", recursive=True)
    print("\n\nfilesin repo path:", files)
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
    response = client.instance.create_artifact(req)

    # remove fork repo
    shutil.rmtree(path)

    # done to make sure we don't loop forever
    return bid_id
