import os

# Tests run offline and deterministically. The actual application defaults to real LLM mode.
os.environ.setdefault("MOCK_LLM_MODE", "true")
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used-in-mock-mode")
