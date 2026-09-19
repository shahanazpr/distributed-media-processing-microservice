from pathlib import Path

ENV_EXAMPLE = Path(__file__).parents[1] / ".env.example"


def test_env_example_does_not_contain_real_credentials():
    content = ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "your-access-key-id" in content
    assert "your-secret-access-key" in content
    assert "your-rabbitmq-username" in content
    assert "your-rabbitmq-password" in content

    assert "AKIA" not in content
    assert "aws_secret_access_key=" not in content.lower() or "your-secret-access-key" in content


def test_env_example_uses_secure_debug_default():
    content = ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "DEBUG=False" in content
