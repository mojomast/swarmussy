import os
import sys

import requests


def test_models(api_key: str, base_url: str) -> None:
    """Call the Requesty /models endpoint to sanity-check the key."""

    endpoint = f"{base_url.rstrip('/')}/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"Testing Requesty key against {endpoint} ...")

    try:
        resp = requests.get(endpoint, headers=headers, timeout=30)
    except Exception as e:  # noqa: BLE001
        print("Request failed:", repr(e))
        sys.exit(1)

    print("Status code:", resp.status_code)
    text = resp.text.strip()
    print("Raw response (first 1000 chars):")
    print(text[:1000])

    if resp.status_code == 200:
        print("\n✅ Key looks valid: /models responded with 200.")
    else:
        print("\n❌ /models did not return 200. Check the response above.")


def test_chat_completions(api_key: str, base_url: str) -> None:
    """Call the Requesty /chat/completions endpoint like the swarm does.

    Uses the same style endpoint and a simple payload with the swarm's
    default model (openai/gpt-5-nano).
    """

    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openai/gpt-5-nano",
        "messages": [
            {"role": "user", "content": "Say hello from a minimal Requesty test."},
        ],
        "temperature": 0.2,
        "max_tokens": 64,
    }

    print("\n---")
    print(f"Testing chat completions against {endpoint} ...")

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    except Exception as e:  # noqa: BLE001
        print("Request failed:", repr(e))
        sys.exit(1)

    print("Status code:", resp.status_code)
    text = resp.text.strip()
    print("Raw response (first 1000 chars):")
    print(text[:1000])

    if resp.status_code == 200:
        print("\n✅ Chat completions looks OK (status 200).")
    else:
        print("\n❌ Chat completions did not return 200. Check if this matches the TUI 403.")


def main() -> None:
    """End-to-end sanity check for your REQUESTY_API_KEY.

    - Reads REQUESTY_API_KEY and optional REQUESTY_BASE_URL from the environment
    - Calls the Requesty /models endpoint
    - Calls the Requesty /chat/completions endpoint with the swarm model
    """

    api_key = os.getenv("REQUESTY_API_KEY")
    base_url = os.getenv("REQUESTY_BASE_URL", "https://router.requesty.ai/v1")

    if not api_key:
        print("REQUESTY_API_KEY is not set in the environment.")
        print("Make sure your .env has a single-line REQUESTY_API_KEY and is being loaded.")
        sys.exit(1)

    print(f"Using REQUESTY_API_KEY prefix: {api_key[:12]}...")
    print(f"Base URL: {base_url}")

    test_models(api_key, base_url)
    test_chat_completions(api_key, base_url)


if __name__ == "__main__":
    main()
