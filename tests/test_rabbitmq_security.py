from pathlib import Path

COMPOSE_FILE = Path(__file__).parents[1] / "docker-compose.yml"


def test_rabbitmq_credentials_are_environment_based():
    content = COMPOSE_FILE.read_text(encoding="utf-8")

    assert "RABBITMQ_USER: ${RABBITMQ_USER}" in content
    assert "RABBITMQ_PASSWORD: ${RABBITMQ_PASSWORD}" in content

    assert "guest" not in content.lower()
    assert "password123" not in content.lower()
