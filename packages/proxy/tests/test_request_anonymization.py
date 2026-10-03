"""
Tests for how the proxy anonymizes request bodies and restores responses.
"""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

import main  # noqa: E402
from prompt_guard import PromptGuard  # noqa: E402


@pytest.fixture
def proxy():
    # Bypass __init__, which connects to Redis.
    instance = main.LLMProxy.__new__(main.LLMProxy)
    instance.guard = PromptGuard()
    return instance


def test_chat_messages_share_one_mapping(proxy):
    # Each message used to be anonymized on its own, so both emails became
    # "[EMAIL_1]" and the response was restored with whichever came last.
    body = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "I am alice@example.com"},
            {"role": "user", "content": "CC bob@example.com, not alice@example.com"},
        ],
    }

    anonymized, mapping = proxy._anonymize_request_body(body, main.LLMProxy.PROVIDERS["openai"])

    assert [m["content"] for m in anonymized["messages"]] == [
        "I am [EMAIL_1]",
        "CC [EMAIL_2], not [EMAIL_1]",
    ]
    assert mapping == {"[EMAIL_1]": "alice@example.com", "[EMAIL_2]": "bob@example.com"}
    # The caller's body is left untouched
    assert body["messages"][0]["content"] == "I am alice@example.com"

    response = {"choices": [{"message": {"content": "Mailed [EMAIL_2] and [EMAIL_1]"}}]}
    restored = proxy._deanonymize_response_body(
        response, mapping, main.LLMProxy.PROVIDERS["openai"]
    )
    assert restored["choices"][0]["message"]["content"] == (
        "Mailed bob@example.com and alice@example.com"
    )


def test_anthropic_system_prompt_and_content_blocks(proxy):
    body = {
        "model": "claude",
        "system": "The customer is alice@example.com",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "My SSN is 123-45-6789"},
                    {"type": "image", "source": {"type": "base64", "data": "AAAA"}},
                ],
            }
        ],
    }

    anonymized, mapping = proxy._anonymize_request_body(
        body, main.LLMProxy.PROVIDERS["anthropic"]
    )

    assert anonymized["system"] == "The customer is [EMAIL_1]"
    blocks = anonymized["messages"][0]["content"]
    assert blocks[0] == {"type": "text", "text": "My SSN is [SSN_1]"}
    assert blocks[1] == body["messages"][0]["content"][1]
    assert mapping == {"[EMAIL_1]": "alice@example.com", "[SSN_1]": "123-45-6789"}
