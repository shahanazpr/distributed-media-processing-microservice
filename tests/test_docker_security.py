from pathlib import Path


COMPOSE_FILE = Path(__file__).parents[1] / "docker-compose.yml"


def test_internal_services_do_not_expose_host_ports():
    content = COMPOSE_FILE.read_text(encoding="utf-8")

    redis_section = content.split("  redis:", 1)[1].split("  rabbitmq:", 1)[0]
    rabbitmq_section = content.split("  rabbitmq:", 1)[1]

    assert "ports:" not in redis_section
    assert "ports:" not in rabbitmq_section


def test_api_exposes_only_application_port():
    content = COMPOSE_FILE.read_text(encoding="utf-8")

    api_section = content.split("  api:", 1)[1].split("  worker:", 1)[0]

    assert 'ports:' in api_section
    assert '"8000:8000"' in api_section