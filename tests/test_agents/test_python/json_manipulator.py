"""
This is a file that writes agent information to a python file

    agent_info = {
        "local_mount_point": code_path,
        "agent_mount_point": "/code",
        "state": "idle",
        "ticket_id": None,
    }

    Then reads from it then edits it

    This is pulled straight from agent_state_mangager.py and edited to have some bugs
"""

import json
import os


class AgentStateManager:
    def __init__(self, code_path):
        self.agent_info = {
            "local_mount_point": code_path,
            "agent_mount_point": "/code",
            "state": "idle",
            "ticket_id": None,
        }
        self.file_path = "agent_state.json"

    def write_to_file(self):
        with open(self.file_path, "w") as file:
            json.dump(self.agent_info, file)

    def read_from_file(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as file:
                self.agent_info = json.load(file)
        else:
            print(f"{self.file_path} does not exist.")

    def update_state(self, state, ticket_id=None):
        self.agent_info["state"] = state
        self.agent_info["ticket_id"] = ticket_id
        self.write_to_file()

    def get_info(self):
        return self.agent_info
