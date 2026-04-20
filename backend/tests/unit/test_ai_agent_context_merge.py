"""Unit tests for AI agent message merge and AG05 snippet formatting."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.services.ai_agent import AIAgentService, CopilotStreamLLM


def test_build_oai_messages_merges_base_and_runtime_system_messages():
    """Base system prompt should be merged with runtime SystemMessage content."""
    llm = CopilotStreamLLM(model="gpt-4o", system_instruction="Base system prompt")

    messages = [
        SystemMessage(content="Runtime AG05 context"),
        HumanMessage(content="What is the status?"),
        AIMessage(content="Current status is stable."),
    ]

    oai_messages = llm._build_oai_messages(messages)

    assert oai_messages == [
        {
            "role": "system",
            "content": "Base system prompt\n\n---\n\nRuntime AG05 context",
        },
        {"role": "user", "content": "What is the status?"},
        {"role": "assistant", "content": "Current status is stable."},
    ]


def test_format_ag05_snippets_formats_lines_with_source_prefix_and_defaults():
    """Formatter should trim values and default missing source IDs to AG05."""
    snippets = [
        {"source_id": " AG05-1 ", "text": "  Alpha context  "},
        {"source_id": "", "text": "Beta context"},
        {"text": "  Gamma context  "},
    ]

    formatted = AIAgentService._format_ag05_snippets(snippets)

    assert formatted == "[AG05-1] Alpha context\n[AG05] Beta context\n[AG05] Gamma context"


def test_format_ag05_snippets_returns_empty_for_empty_or_blank_text_items():
    """Formatter should return empty string when there is no usable snippet text."""
    assert AIAgentService._format_ag05_snippets([]) == ""
    assert AIAgentService._format_ag05_snippets(
        [
            {"source_id": "AG05-1", "text": "   "},
            {"source_id": "AG05-2", "text": ""},
            {"source_id": "AG05-3"},
        ]
    ) == ""