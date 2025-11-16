"""
FastAPI example demonstrating llm-slm-prompt-guard integration.

This example shows how to use PromptGuard to anonymize user prompts
before sending them to an LLM and de-anonymize the responses.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add the package to the path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../packages/python/src"))

from prompt_guard import PromptGuard

# Uncomment to use with actual LLM
# from openai import OpenAI

app = FastAPI(
    title="LLM/SLM Prompt Guard Demo",
    description="FastAPI demo of PII anonymization for LLM applications",
    version="0.1.0",
)

# Initialize PromptGuard
guard = PromptGuard(detectors=["regex"], policy="default_pii")

# Uncomment to use with actual LLM
# client = OpenAI()


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = "gpt-4o-mini"
    use_mock: Optional[bool] = True  # Set to False to use real LLM


class ChatResponse(BaseModel):
    answer: str
    anonymized_prompt: str
    detected_pii: dict


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "LLM/SLM Prompt Guard API is running",
        "version": "0.1.0",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Process a chat request with PII anonymization.

    The flow:
    1. Anonymize the user's prompt
    2. Send anonymized prompt to LLM
    3. De-anonymize the LLM's response
    4. Return the final response
    """
    try:
        # Step 1: Anonymize the prompt
        anonymized, mapping = guard.anonymize(req.prompt)

        # Step 2: Send to LLM (mocked or real)
        if req.use_mock:
            # Mock LLM response for demo purposes
            answer = f"This is a mock response to: {anonymized}"
        else:
            # Uncomment to use real OpenAI
            # completion = client.chat.completions.create(
            #     model=req.model,
            #     messages=[{"role": "user", "content": anonymized}],
            # )
            # answer = completion.choices[0].message.content or ""
            raise HTTPException(
                status_code=400,
                detail="Real LLM integration not configured. Set use_mock=true or configure OpenAI API key.",
            )

        # Step 3: De-anonymize the response
        final_answer = guard.deanonymize(answer, mapping)

        return ChatResponse(
            answer=final_answer,
            anonymized_prompt=anonymized,
            detected_pii={
                "count": len(mapping),
                "types": list(set(k.split("_")[0][1:] for k in mapping.keys())),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/anonymize")
async def anonymize(req: ChatRequest):
    """
    Endpoint to only anonymize text without calling LLM.
    Useful for testing the anonymization functionality.
    """
    try:
        anonymized, mapping = guard.anonymize(req.prompt)
        return {
            "original": req.prompt,
            "anonymized": anonymized,
            "mapping": mapping,
            "pii_detected": len(mapping),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
