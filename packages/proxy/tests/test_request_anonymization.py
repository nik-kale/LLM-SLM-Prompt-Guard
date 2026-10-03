"""
Tests for how the proxy anonymizes request bodies and restores responses.
"""

import asyncio
import json

import pytest

pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

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


def test_rewritten_bodies_do_not_carry_stale_headers():
    request_headers = {
        "Host": "proxy.local",
        "Content-Length": "120",
        "Authorization": "Bearer sk-test",
        "X-User-ID": "alice",
        "Content-Type": "application/json",
    }
    response_headers = {
        "content-length": "999",
        "content-encoding": "gzip",
        "content-type": "application/json",
        "x-request-id": "abc",
    }

    assert main._filter_headers(request_headers, main._REQUEST_HEADERS_TO_DROP) == {
        "Authorization": "Bearer sk-test",
        "Content-Type": "application/json",
    }
    assert main._filter_headers(response_headers, main._RESPONSE_HEADERS_TO_DROP) == {
        "content-type": "application/json",
        "x-request-id": "abc",
    }


def test_config_is_read_from_environment(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379")
    monkeypatch.setenv("POLICY", "gdpr_strict")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("TRUSTED_IPS", "10.0.0.1, 10.0.0.2")

    config = main.ProxyConfig.from_env()

    assert config.redis_url == "redis://redis:6379"
    assert config.policy == "gdpr_strict"
    assert config.port == 9000
    assert config.trusted_ips == ["10.0.0.1", "10.0.0.2"]


def test_streaming_response_is_deanonymized_per_event(proxy):
    # The whole SSE body used to be treated as one event; json.loads failed
    # and the placeholders were passed through unchanged.
    events = [
        {"choices": [{"delta": {"content": "Hello [NAME_1]"}}]},
        {"choices": [{"delta": {"content": ", mail [EMAIL_1]"}}]},
    ]
    body = "".join(f"data: {json.dumps(e)}\n\n" for e in events) + "data: [DONE]\n\n"
    upstream = httpx.Response(
        200,
        content=body.encode(),
        headers={"content-type": "text/event-stream", "content-length": str(len(body))},
    )
    mapping = {"[NAME_1]": "Jane Doe", "[EMAIL_1]": "jane@example.com"}

    async def collect():
        response = await proxy._handle_streaming_response(upstream, mapping, "session")
        chunks = [chunk async for chunk in response.body_iterator]
        return response, b"".join(chunks).decode()

    response, streamed = asyncio.run(collect())

    contents = [
        json.loads(line[6:])["choices"][0]["delta"]["content"]
        for line in streamed.splitlines()
        if line.startswith("data: {")
    ]
    assert contents == ["Hello Jane Doe", ", mail jane@example.com"]
    assert "data: [DONE]" in streamed
    assert "content-length" not in response.headers
