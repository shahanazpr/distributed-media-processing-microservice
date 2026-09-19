from app.core.config import Settings


def test_security_defaults():
    settings = Settings(_env_file=None)

    assert settings.debug is False
    assert settings.rabbitmq_user == ""
    assert settings.rabbitmq_password == ""