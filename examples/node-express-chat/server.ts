/**
 * Express example demonstrating llm-slm-prompt-guard integration.
 *
 * This example shows how to use PromptGuard to anonymize user prompts
 * before sending them to an LLM/SLM and de-anonymize the responses.
 */

import express, { Request, Response } from "express";
import { PromptGuard, createPromptGuard } from "../../packages/node/src";
// Uncomment to use with actual LLM
// import OpenAI from "openai";

const app = express();
app.use(express.json());

// Initialize PromptGuard
const guard = createPromptGuard({
  detectors: ["regex"],
  policy: "default_pii",
});

// Uncomment to use with actual LLM
// const openai = new OpenAI({
//   apiKey: process.env.OPENAI_API_KEY,
// });

interface ChatRequest {
  prompt: string;
  model?: string;
  useMock?: boolean;
}

interface ChatResponse {
  answer: string;
  anonymizedPrompt: string;
  detectedPII: {
    count: number;
    types: string[];
  };
}

// Health check
app.get("/", (req: Request, res: Response) => {
  res.json({
    status: "healthy",
    message: "LLM/SLM Prompt Guard API is running",
    version: "0.1.0",
  });
});

// Main chat endpoint
app.post("/chat", async (req: Request, res: Response) => {
  try {
    const { prompt, model = "gpt-4o-mini", useMock = true }: ChatRequest = req.body;

    if (!prompt) {
      return res.status(400).json({ error: "Prompt is required" });
    }

    // Step 1: Anonymize the prompt
    const { anonymized, mapping } = guard.anonymize(prompt);

    // Step 2: Send to LLM (mocked or real)
    let answer: string;

    if (useMock) {
      // Mock LLM response for demo purposes
      answer = `This is a mock response to: ${anonymized}`;
    } else {
      // Uncomment to use real OpenAI
      // const completion = await openai.chat.completions.create({
      //   model,
      //   messages: [{ role: "user", content: anonymized }],
      // });
      // answer = completion.choices[0].message?.content ?? "";
      return res.status(400).json({
        error:
          "Real LLM integration not configured. Set useMock=true or configure OpenAI API key.",
      });
    }

    // Step 3: De-anonymize the response
    const finalAnswer = guard.deanonymize(answer, mapping);

    // Extract PII types from mapping
    const piiTypes = Array.from(
      new Set(
        Object.keys(mapping).map((key) => {
          const match = key.match(/\[([A-Z_]+)_\d+\]/);
          return match ? match[1] : "UNKNOWN";
        })
      )
    );

    const response: ChatResponse = {
      answer: finalAnswer,
      anonymizedPrompt: anonymized,
      detectedPII: {
        count: Object.keys(mapping).length,
        types: piiTypes,
      },
    };

    res.json(response);
  } catch (error) {
    console.error("Error processing chat request:", error);
    res.status(500).json({
      error: error instanceof Error ? error.message : "Internal server error",
    });
  }
});

// Anonymize-only endpoint
app.post("/anonymize", (req: Request, res: Response) => {
  try {
    const { prompt }: { prompt: string } = req.body;

    if (!prompt) {
      return res.status(400).json({ error: "Prompt is required" });
    }

    const { anonymized, mapping } = guard.anonymize(prompt);

    res.json({
      original: prompt,
      anonymized,
      mapping,
      piiDetected: Object.keys(mapping).length,
    });
  } catch (error) {
    console.error("Error anonymizing:", error);
    res.status(500).json({
      error: error instanceof Error ? error.message : "Internal server error",
    });
  }
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/`);
  console.log(`Try: curl -X POST http://localhost:${PORT}/anonymize -H "Content-Type: application/json" -d '{"prompt":"Hi, I am John Smith"}'`);
});
