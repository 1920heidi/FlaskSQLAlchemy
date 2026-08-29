import pytest

from app import app as flask_app
from models import db


@pytest.fixture
def app():
    flask_app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        TESTING=True,
    )
    with flask_app.app_context():
        db.create_all()
        try:
            yield flask_app
        finally:
            db.session.rollback()
            db.session.remove()
            db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
