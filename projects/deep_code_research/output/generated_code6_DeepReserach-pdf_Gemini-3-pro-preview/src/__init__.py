"""
DeepResearch Framework
======================

A modular, scalable, and verifiable multimodal deep research framework.
This package provides the core components for building autonomous research agents
capable of planning, information acquisition, memory management, and reasoning 
over multimodal data.

The framework is structured into four key components:
1. Query Planning (Planner)
2. Information Acquisition (Executor)
3. Memory Management (ResearchSession)
4. Answer Generation (Coordinator/Reviewer)
"""

import logging
from typing import List

# Configure a NullHandler to suppress logging warnings if the application
# does not configure logging.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "1.0.0"
__author__ = "DeepResearch Team"

# ---------------------------------------------------------------------------
# Core Abstractions & Data Models
# ---------------------------------------------------------------------------
# Expose the main session context and base classes
from .core.session import ResearchSession
from .core.base import ResearchAgent
from .core.task import Task
from .core.evidence import Evidence

# ---------------------------------------------------------------------------
# Agent Components
# ---------------------------------------------------------------------------
# Expose the agents responsible for the research lifecycle
from .agents.coordinator import Coordinator
from .agents.planner import Planner
from .agents.executor import Executor
from .agents.reviewer import Reviewer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
from .config import Config

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
__all__: List[str] = [
    "ResearchSession",
    "ResearchAgent",
    "Task",
    "Evidence",
    "Coordinator",
    "Planner",
    "Executor",
    "Reviewer",
    "Config",
]