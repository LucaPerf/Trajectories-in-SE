"""Automata learning from agent traces.

This package provides tools for:
1. Extracting interaction sequences from pentesting run databases
2. Abstracting concrete interactions into categorical representations via LLM
3. Learning Markov chains / MDPs from abstract traces using AALpy
4. Extracting strategic hints and transfer knowledge from learned models
"""

from .knowledge_models import Interaction, RunData, AbstractionsFile
from .trace_extraction import extract_sequences, build_concretization
from .abstraction import categorize_interactions, normalize_categories, abstract_sequence
from .automaton_learning import traces_to_aalpy, learn_automaton, save_learned_model, learn_and_save
from .knowledge_extraction import (
    extract_hints,
    extract_transfer_knowledge,
    extract_common_path,
    extract_guided_hints,
    model_has_success,
    summarize_model,
    describe_model,
    prune_model,
    prune_model_multi,
    goms_slice,
    goms_dag,
    goms_topk,
)
from .dynamic_guidance import DynamicGuidance

__all__ = [
    "Interaction",
    "RunData",
    "AbstractionsFile",
    "extract_sequences",
    "build_concretization",
    "categorize_interactions",
    "normalize_categories",
    "abstract_sequence",
    "traces_to_aalpy",
    "learn_automaton",
    "save_learned_model",
    "learn_and_save",
    "extract_hints",
    "extract_transfer_knowledge",
    "extract_common_path",
    "extract_guided_hints",
    "model_has_success",
    "summarize_model",
    "describe_model",
    "prune_model",
    "prune_model_multi",
    "goms_slice",
    "goms_dag",
    "goms_topk",
    "DynamicGuidance",
]
