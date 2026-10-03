# Tool-Using Research Agent

A bounded, evidence-grounded research agent built with **Python, LangGraph, LangChain, and OpenAI**.

The agent receives a research question, discovers relevant web sources, fetches source pages, builds an evidence set from successfully retrieved content, and produces a cited final answer.

The implementation was developed for the **AgenticX AI Labs AI Agents & Automation internship — Project Brief 1: Tool-Using Research Agent**.

---

## What This Project Demonstrates

This project demonstrates a tool-using research agent with:

- Two distinct web tools
- Explicit LangGraph state
- LLM-driven tool selection
- Search → fetch → evidence → answer workflow
- A configurable hard step limit
- Graceful handling of tool failures
- Evidence restricted to successfully fetched pages
- Inline source citations
- Automated tests for normal and failure conditions

---

## Architecture

```text
                    ┌─────────────────────┐
                    │   User Research     │
                    │      Question       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Research Agent     │
                    │    LangGraph Node   │
                    └──────────┬──────────┘
                               │
                         Tool requested?
                          /            \
                        yes             no
                        │                │
                        ▼                ▼
              ┌────────────────┐   ┌──────────────┐
              │ Execute Tools  │   │   Finalize   │
              └───────┬────────┘   └──────┬───────┘
                      │                   │
                      │                   ▼
                      │          Evidence-grounded
                      │             final answer
                      │                   │
                      ▼                   ▼
               ┌──────────────┐         END
               │ search_web   │
               │ fetch_page   │
               └──────┬───────┘
                      │
                      ▼
                Tool results
                      │
                      ▼
               Research Agent
                  (loop)

              Hard step limit
                     │
                     ▼
                  Finalize