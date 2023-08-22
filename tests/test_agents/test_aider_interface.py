import pytest
import os
import subprocess
from pathlib import Path
import shutil

from agent_harness.aider_config.aider_interface import (
    _get_python_files,
    register_agent,
    start_agent_task,
)

from tests.test_agents.verification_python.sum_checker import check_two_sum
from tests.test_agents.test_python.sum import two_sum


@pytest.fixture
def test_data_dir(tmp_path):
    test_dir = tmp_path / "test_data"
    test_dir.mkdir(exist_ok=True)

    # Ensure the directory is empty
    for file_name in os.listdir(test_dir):
        file_path = os.path.join(test_dir, file_name)
        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

    # Add some Python files to the root directory
    for i in range(3):
        with open(test_dir / f"file{i}.py", "w") as file:
            file.write(f"print('file{i}')")

    # Create nested directories and add Python files
    nested_dir1 = test_dir / "nested1"
    nested_dir1.mkdir()
    with open(nested_dir1 / "nested_file.py", "w") as file:
        file.write("print('nested_file')")

    nested_dir2 = nested_dir1 / "nested2"
    nested_dir2.mkdir()
    with open(nested_dir2 / "deeply_nested_file.py", "w") as file:
        file.write("print('deeply_nested_file')")

    return test_dir


def test_get_python_files(test_data_dir):
    mount_point = "/code"
    code_path = str(test_data_dir)

    expected_files = [f"{mount_point}/file{i}.py" for i in range(3)] + [
        f"{mount_point}/nested1/nested_file.py",
        f"{mount_point}/nested1/nested2/deeply_nested_file.py",
    ]

    actual_files = _get_python_files(mount_point, code_path)

    assert sorted(actual_files) == sorted(
        expected_files
    ), f"Expected {expected_files}, but got {actual_files}"


def test_aider_can_change_code():
    # Get the directory of the current file
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # Define the code path and register the agent
    code_path = current_dir / "test_python"
    register_agent(code_path, current_dir.parent.parent)

    try:
        check_two_sum()
        # this should raise an assertion error if it doesn't, then we can't test the agent
        raise ValueError("The test should fail before the code is changed")
    except AssertionError:
        # The test should fail
        pass

    # Suppose the task text describes the bug that needs to be fixed
    task_text = f"Fix the `two_sum` function so that it adds values correctly."

    # Perform the task
    start_agent_task(task_text)

    # Run the same test again and assert that it now passes
    check_two_sum()
