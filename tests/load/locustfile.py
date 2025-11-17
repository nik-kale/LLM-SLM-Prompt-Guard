"""
Load testing for llm-slm-prompt-guard HTTP proxy.

This Locust file tests the HTTP proxy under various load conditions to validate
performance, scalability, and reliability.

Installation:
    pip install locust

Usage:
    # Start proxy
    python packages/proxy/src/main.py

    # Run load test
    locust -f tests/load/locustfile.py --host=http://localhost:8000

    # Or with web UI
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --web-host=0.0.0.0

    # Headless mode (10 users, 2 per second spawn rate, 60 seconds)
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --users 10 --spawn-rate 2 --run-time 60s --headless

    # Heavy load test
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 300s --headless
"""

from locust import HttpUser, task, between, events
import random
import json
import time
from typing import List


# Sample test data with varying PII complexity
SAMPLE_TEXTS = [
    # Simple (1-2 PII items)
    "Contact me at john@example.com",
    "Call me at 555-123-4567",
    "My name is Alice Johnson",

    # Medium (3-5 PII items)
    "Hi, I'm Dr. Sarah Johnson. Email: sarah@hospital.com, Phone: 555-0123",
    "John Smith (SSN: 123-45-6789) at john@example.com needs help",
    "Contact: Bob Williams, Email: bob@company.com, Phone: 555-9876",

    # Complex (5+ PII items)
    """
    Patient: Jane Doe
    DOB: 1985-03-15
    SSN: 987-65-4321
    Email: jane.doe@email.com
    Phone: 555-1234
    Address: 123 Main St, Boston, MA
    """,
    """
    Employee: Michael Chen
    Employee ID: EMP-12345
    Email: m.chen@company.com
    Phone: +1-555-0100
    Credit Card: 4532-1234-5678-9010
    """,
]

# OpenAI API request templates
OPENAI_CHAT_TEMPLATE = {
    "model": "gpt-4",
    "messages": [],
    "temperature": 0.7,
}

OPENAI_COMPLETION_TEMPLATE = {
    "model": "gpt-3.5-turbo-instruct",
    "prompt": "",
    "max_tokens": 100,
}


class PromptGuardUser(HttpUser):
    """
    Simulates a user sending requests through the prompt-guard proxy.

    This user performs various tasks with different weights to simulate
    realistic traffic patterns.
    """

    # Wait between 1-3 seconds between requests (adjust for your use case)
    wait_time = between(1, 3)

    def on_start(self):
        """Initialize user session."""
        self.session_id = None
        self.pii_count = 0
        self.request_count = 0

    @task(10)
    def health_check(self):
        """
        Check health endpoint (high frequency).

        Weight: 10 (most common request)
        """
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def metrics_check(self):
        """
        Check metrics endpoint (medium frequency).

        Weight: 5
        """
        with self.client.get(
            "/metrics",
            catch_response=True,
            name="/metrics"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.pii_count = data.get("pii_detected", 0)
                    response.success()
                except:
                    response.failure("Invalid metrics response")
            else:
                response.failure(f"Metrics check failed: {response.status_code}")

    @task(30)
    def openai_chat_completion(self):
        """
        Send OpenAI chat completion request with PII (highest frequency).

        Weight: 30 (primary use case)
        """
        text = random.choice(SAMPLE_TEXTS)
        request_payload = OPENAI_CHAT_TEMPLATE.copy()
        request_payload["messages"] = [
            {"role": "user", "content": text}
        ]

        start_time = time.time()

        with self.client.post(
            "/openai/v1/chat/completions",
            json=request_payload,
            headers={
                "Content-Type": "application/json",
                "X-User-ID": f"user_{self.environment.runner.user_count}"
            },
            catch_response=True,
            name="/openai/v1/chat/completions"
        ) as response:
            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                try:
                    data = response.json()
                    # Verify response structure
                    if "choices" in data and len(data["choices"]) > 0:
                        self.request_count += 1
                        response.success()

                        # Log high latency
                        if latency > 1000:
                            events.request.fire(
                                request_type="WARNING",
                                name="high_latency_chat",
                                response_time=latency,
                                response_length=len(response.content),
                                exception=None,
                                context={}
                            )
                    else:
                        response.failure("Invalid response structure")
                except Exception as e:
                    response.failure(f"Response parsing error: {e}")
            else:
                response.failure(f"Request failed: {response.status_code}")

    @task(15)
    def openai_completion(self):
        """
        Send OpenAI completion request (medium frequency).

        Weight: 15
        """
        text = random.choice(SAMPLE_TEXTS)
        request_payload = OPENAI_COMPLETION_TEMPLATE.copy()
        request_payload["prompt"] = text

        with self.client.post(
            "/openai/v1/completions",
            json=request_payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="/openai/v1/completions"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Request failed: {response.status_code}")

    @task(2)
    def anthropic_chat(self):
        """
        Send Anthropic messages request (low frequency).

        Weight: 2
        """
        text = random.choice(SAMPLE_TEXTS)
        request_payload = {
            "model": "claude-3-opus-20240229",
            "messages": [
                {"role": "user", "content": text}
            ],
            "max_tokens": 100,
        }

        with self.client.post(
            "/anthropic/v1/messages",
            json=request_payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="/anthropic/v1/messages"
        ) as response:
            if response.status_code in [200, 404]:  # 404 if not configured
                response.success()
            else:
                response.failure(f"Request failed: {response.status_code}")

    @task(5)
    def batch_requests(self):
        """
        Send multiple requests in quick succession (burst traffic).

        Weight: 5
        """
        for _ in range(3):
            text = random.choice(SAMPLE_TEXTS)
            request_payload = OPENAI_CHAT_TEMPLATE.copy()
            request_payload["messages"] = [
                {"role": "user", "content": text}
            ]

            self.client.post(
                "/openai/v1/chat/completions",
                json=request_payload,
                headers={"Content-Type": "application/json"},
                name="/openai/v1/chat/completions (batch)"
            )

            # Small delay between batch requests
            time.sleep(0.1)


class HeavyUser(HttpUser):
    """
    Simulates a heavy user with high request volume.

    This user type is used for stress testing.
    """

    wait_time = between(0.1, 0.5)  # Much faster requests

    @task
    def continuous_chat(self):
        """Send continuous chat requests."""
        text = random.choice(SAMPLE_TEXTS)
        request_payload = OPENAI_CHAT_TEMPLATE.copy()
        request_payload["messages"] = [
            {"role": "user", "content": text}
        ]

        self.client.post(
            "/openai/v1/chat/completions",
            json=request_payload,
            headers={"Content-Type": "application/json"},
        )


# Event handlers for custom metrics

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize custom metrics."""
    print("\n" + "="*60)
    print("Load Test Starting - llm-slm-prompt-guard")
    print("="*60)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.parsed_options.num_users if hasattr(environment, 'parsed_options') else 'N/A'}")
    print("="*60 + "\n")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("🚀 Load test started")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops - print summary."""
    print("\n" + "="*60)
    print("Load Test Summary")
    print("="*60)

    stats = environment.stats

    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"\nAverage Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Median Response Time: {stats.total.median_response_time:.2f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")

    print(f"\nRequests/sec: {stats.total.total_rps:.2f}")
    print(f"Current RPS: {stats.total.current_rps:.2f}")

    print("\n" + "="*60)

    # Check if performance targets are met
    if stats.total.avg_response_time < 100:
        print("✅ PASS: Average response time < 100ms")
    else:
        print("❌ FAIL: Average response time >= 100ms")

    if stats.total.fail_ratio < 0.01:  # Less than 1% failure
        print("✅ PASS: Failure rate < 1%")
    else:
        print("❌ FAIL: Failure rate >= 1%")

    print("="*60 + "\n")


# Custom shapes for different load patterns

from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    Step load pattern - gradually increase load in steps.

    Useful for finding the breaking point.
    """

    step_time = 60  # seconds per step
    step_load = 10  # users to add per step
    max_users = 100

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.step_time * (self.max_users // self.step_load):
            return None

        current_step = run_time // self.step_time
        user_count = min(self.step_load * (current_step + 1), self.max_users)

        return (user_count, user_count)


class SpikeLoadShape(LoadTestShape):
    """
    Spike load pattern - sudden traffic spikes.

    Simulates sudden bursts of traffic.
    """

    def tick(self):
        run_time = self.get_run_time()

        # Normal load: 10 users
        # Spike at 60s, 180s, 300s: 100 users for 20 seconds
        if 60 <= run_time < 80 or 180 <= run_time < 200 or 300 <= run_time < 320:
            return (100, 50)  # Spike
        elif run_time < 360:
            return (10, 5)  # Normal
        else:
            return None
