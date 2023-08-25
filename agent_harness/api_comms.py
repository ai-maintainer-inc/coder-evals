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
from pprint import pprint
import uuid
from pathlib import Path
import os
import time
import shutil

# update this import to use your interface here!
from agent_harness.aider_config.aider_interface import register_agent, start_agent_task
from agent_harness.gitutil import GitRepo, create_url


API_HOST = "http://marketplace-api:8080/api/v1"
GIT_HOST = "http://git-server:8080"
CLIENT_USERNAME = "test_user1"
CLIENT_PASSWORD = "F@k3awefawefawef"
CLIENT_CODE_OWNER = CLIENT_USERNAME
CLIENT_CODE_REPO = "repo1"
OPERATOR_USERNAME = "test_user2"
OPERATOR_PASSWORD = "F@k3awefawefawef"
OPERATOR_CODE_OWNER = OPERATOR_USERNAME
OPERATOR_CODE_REPO = "repo2"
TEMP_DIR = "./deleteme"

BENCHMARK_IDS = ["dc13a85a-9a5f-4da1-924f-d965cf0982cc"]


class PythonClientUser:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.cfg = openapi_client.Configuration(
            host=API_HOST,
            username=self.username,
            password=self.password,
        )
        self.api = openapi_client.ApiClient(self.cfg)
        self.instance = default_api.DefaultApi(self.api)


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
    return response.body


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


def create_artifacts(client, agent_id):
    """
    This calls the agent!
    Modify the call to the agent here.
    """
    # get agent bids
    response = client.instance.get_agent_bids(
        query_params={
            "agentId": agent_id,
            "status": "pending",
        }
    )
    bids = list(response.body["bids"])
    if len(bids) == 0:
        return None
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
        return None
    print("ticket:", ticket)
    # get the code from the ticket
    code = ticket["code"]

    # fork the code
    req = models.CreateRepositoryRequest(
        repositoryName=OPERATOR_CODE_REPO,
        isPublic=False,
    )
    try:
        response = client.instance.create_repository(req)
        assert response.response.status == 201
    except openapi_client.ApiException as e:
        assert e.status == 409

    url = create_url(GIT_HOST, code["owner"], code["repo"])
    gitrepo = GitRepo(url, OPERATOR_USERNAME, OPERATOR_PASSWORD)
    fork_url = create_url(GIT_HOST, OPERATOR_CODE_OWNER, OPERATOR_CODE_REPO)
    gitrepo.fork(fork_url, force=True)
    fork = GitRepo(fork_url, OPERATOR_USERNAME, OPERATOR_PASSWORD)
    path = os.environ["CODE_PATH"]
    print("path:", path)
    fork.clone(path)
    start_agent_task(ticket["description"])

    fork.add(path, all=True)
    if fork.has_changes(path):
        fork.commit(path, "add README.md")
        fork.push(path)

    # create artifact
    req = models.CreateArtifactRequest(
        bidId=bid_id,
        code=models.Code(
            owner=OPERATOR_CODE_OWNER,
            repo=OPERATOR_CODE_REPO,
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

    # # create artifact
    # req = models.CreateArtifactRequest(
    #     bidId=bid_id,
    #     code=models.Code(
    #         owner=OPERATOR_CODE_OWNER,
    #         repo=OPERATOR_CODE_REPO,
    #         branch="",
    #         commit="",
    #     ),
    #     draft=False,
    # )
    # response = operator.instance.create_artifact(req)


def main():
    # Generate sample agent_data
    client = PythonClientUser(OPERATOR_USERNAME, OPERATOR_PASSWORD)

    # env variables for the aider path and code path are both defined as env variables in the dockerfile.
    # CODE_PATH and AIDER_PATH respectively.
    code_path = Path(os.environ.get("CODE_PATH"))
    aider_path = Path(os.environ.get("AIDER_PATH"))
    agent_name = "aiderUnique"

    json_path = register_agent(code_path, aider_path, agent_name)
    list_agents = get_agents(client)
    pprint(list_agents)
    agent_id = check_if_agent_exists(client, agent_name)
    if not agent_id:
        print("Agent does not exist. Creating.")
        agent_id = api_register_agent(client, "aiderUnique")
        pprint(agent_id)

    for bench_id in BENCHMARK_IDS:
        req = models.CreateBenchmarkTicketRequest(
            agentId=agent_id,
            benchmarkId=bench_id,
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
                bid_id = create_artifacts(client, agent_id)
                print("bid_id:", bid_id)
                if bid_id:
                    return

            time.sleep(2)


if __name__ == "__main__":
    main()
