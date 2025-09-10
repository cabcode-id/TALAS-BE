# tests/conftest.py
import pytest
from app import create_app, db
from app.model import Title, Article
from datetime import date

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

@pytest.fixture
def client():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        # seed data
        title = Title(
            title_index=1,
            title="Sample News",
            image="img.png",
            all_summary="Summary",
            date=date.today(),
            cluster="cluster-a",
            analysis="analysis"
        )
     
        article = Article(
            title="Article 1",
            url="http://example.com",
            source="Kompas",
            date=date.today(),
            bias=0.2,
            hoax=False,
            ideology=0.3,
            title_index=1
        )
        article1 = Article(
            title="Article 2",
            url="http://example.com",
            source="ExampleSource",
            date=date.today(),
            bias=0.2,
            hoax=False,
            ideology=0.3,
            title_index=1
        )
        article2 = Article(
            title="Article 3",
            url="http://example.com",
            source="ExampleSource",
            date=date.today(),
            bias=0.2,
            hoax=False,
            ideology=0.3,
            title_index=1
        )

        db.session.add_all([article,article1, article2, title])
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()
