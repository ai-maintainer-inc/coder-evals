import json
import pytest
from tests.test_agents.test_aider_interface import (
    AgentStateManager,
)  # Assuming the class is defined in agent_state_manager.py


class TestAgentStateManager:
    @pytest.fixture
    def agent_state_manager(self):
        return AgentStateManager("/test_code_path")

    # def test_reading_non_existent_file(self, agent_state_manager):
    #     agent_state_manager.read_from_file()
    #     assert (
    #         agent_state_manager.get_info() is not None
    #     ), "Agent info should be initialized even if file does not exist"

    def test_overwrite_of_non_updated_fields(self, agent_state_manager, tmp_path):
        agent_state_manager.file_path = str(tmp_path / "test.json")
        agent_state_manager.agent_info["extra_field"] = "extra_value"
        agent_state_manager.write_to_file()
        agent_state_manager.agent_info.pop("extra_field")
        agent_state_manager.read_from_file()
        assert (
            "extra_field" in agent_state_manager.get_info()
        ), "Non-updated fields should not be overwritten"

    # def test_lack_of_validation_on_state_change(self, agent_state_manager):
    #     invalid_state = "INVALID_STATE"
    #     agent_state_manager.update_state(invalid_state)
    #     assert (
    #         agent_state_manager.get_info()["state"] != invalid_state
    #     ), "Invalid states should not be accepted"

    # def test_file_writing_collision(self, agent_state_manager, tmp_path):
    #     agent_state_manager.file_path = str(tmp_path / "test.json")
    #     other_agent_state_manager = AgentStateManager("/test_code_path")
    #     other_agent_state_manager.file_path = str(tmp_path / "test.json")

    #     agent_state_manager.update_state("working")
    #     other_agent_state_manager.update_state("idle")

    #     with open(agent_state_manager.file_path, "r") as file:
    #         file_content = json.load(file)
    #         assert (
    #             file_content["state"] != "working"
    #         ), "File writing collision should be handled"
