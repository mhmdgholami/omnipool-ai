from pathlib import Path

FORBIDDEN = (
    "api.openai.com",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
)


def test_paid_ai_credentials_and_endpoints_are_not_in_runtime_code():
    paths = list(Path("backend").rglob("*.py"))
    paths.append(Path(".env.example"))

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in paths
    )

    for forbidden in FORBIDDEN:
        assert forbidden not in combined
