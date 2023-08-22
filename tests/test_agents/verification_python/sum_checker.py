import json
import pytest
from pathlib import Path
import importlib


def check_two_sum():
    my_sum_module = importlib.import_module("tests.test_agents.test_python.sum")
    importlib.reload(my_sum_module)
    two_sum = my_sum_module.two_sum
    assert two_sum(1, 2) == 3
    assert two_sum(2, 2) == 4
    assert two_sum(0, 0) == 0
    assert two_sum(-1, 1) == 0
    assert two_sum(-1, -1) == -2
