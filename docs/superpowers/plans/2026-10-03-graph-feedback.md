# Specific discovery and feedback Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for the core and notebook; graph import is an independent parallel task. Steps use checkbox syntax for tracking.

**Goal:** Sourced concrete recommendations with independent curiosity, familiarity and difficulty feedback.

**Architecture:** A fixed graph snapshot feeds a reusable graph selector; a local profile adjusts ranking while hard eligibility remains in force. The notebook uses both existing broad search and the new second stage.

**Tech Stack:** Existing Python, NumPy, Sentence Transformers, requests, ipywidgets, nbclient.

**Spec:** [graph-feedback-design.md](../../graph-feedback-design.md)

## Global Constraints

- Preserve sentence-transformers/all-mpnet-base-v2 and the user's MPS setting.
- Preserve edited notebook interests/settings; no web app or external accounts.
- Real category edges must carry sources. Levels are editorial, never graph depth.
- Keep personal feedback local and ignored by Git.

## Review Focus

- Cycles/multiple paths: finite traversal and no duplicate concept recommendations.
- Sparse bands: fewer results, no radius widening, actual overlap cap maintained.
- Combined curious/hard feedback: affinity retained and local challenge adjusted.
- Unknown levels: no inferred mastery or fabricated prerequisite relationships.
- Repeat saves/restarts: one latest rating per concept and atomic profile persistence.

## Tasks

- [x] Graph importer: scripts/import_discovery_graph.py, data/discovery_graph.json, data/discovery_seeds.json, tests/test_graph_import.py. Actual source paths, bounded/cached requests, balanced roots and explicit missing coverage.
- [x] Profile: feedback.py and tests/test_feedback.py. new_profile(), set_feedback(profile, concept_id, *, curious, known, difficulty, level, area_ids), load_profile(path), save_profile(profile,path), clear_feedback(profile,concept_id), record_exposures(profile,rows). Test independent axes and persistence before implementation.
- [x] Selector: graph_explorer.py and tests/test_graph_explorer.py. load_graph(path), graph_candidates(graph,area_ids,max_depth), select_areas(areas,area_vectors,query_vectors,limit), recommend_specific(graph,concept_vectors,interests,interest_vectors,*,area_ids,profile,settings). Test bounds, graph traversal, known exclusions, difficulty/curiosity reranking, exploration reserve and randomization before implementation.
- [x] Notebook: append graph/feedback cells; embed snapshot once; independent feedback controls, paths, score explanations, live reranking, offline synthetic feedback comparison and local profile storage.
- [x] Run all tests, execute the full notebook with real MPNet, verify UI feedback callbacks with a temporary profile, document usage and known limits, review final diff.

## Verification result

The later balance correction supersedes the initial snapshot counts below:
all 23 original domains now have three areas, 160 runtime-eligible concepts,
and two reviewed entries at each of three levels. The graph contains 3,642
unique concepts and 3,919 verified source edges. The cached rebuild is identical.
All 81 tests pass, including domain-budget and cross-path leakage regressions.
No seed-specific depth exception remains.

Completed on 2026-10-03. All 74 tests pass. The full notebook executed with the
existing local MPNet/MPS configuration and retained the user's original experiment
cells. Real widget callbacks verified combined curiosity/known/difficulty feedback,
local persistence, undo, and invalid-input recovery using a temporary profile.
The before/after example moves from a technical interactive-proof entry toward a
reviewed level-2 Turing-machine entry after curious + too-hard feedback.

The snapshot contains 2,605 concepts, 154 categories, 30 areas and 2,846 sourced
edges. Every edge was checked against cached source membership; the cached offline
rebuild matches the saved snapshot. A reviewed difficulty level is available for
54 concepts; other levels remain explicitly unknown. Independent review found
and regression-tested two fixes: stable per-concept noise after known exclusions,
and transactional exposure updates when profile writes fail.
