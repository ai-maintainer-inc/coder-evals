"""Top-level package for Agent Harness."""

__author__ = """AI Maintainer"""
__email__ = "douglas@ai-maintainer.com"
# fmt: off
__version__ = '0.1.1'
# fmt: on

from .agent_harness import (
    maybe_register_user,
    maybe_create_agent,
    get_benchmark_ids,
    StartBenchmarkResult,
    start_benchmark,
    ask_question,
    submit_artifact,
)
