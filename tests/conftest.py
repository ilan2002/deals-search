import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db import get_session, init_db
from app.ingestion.connectors.sample import SampleFeedConnector
from app.ingestion.service import ingest
from app.main import app


@pytest.fixture
def settings():
    return Settings(amazon_associate_tag="dealsearch-21", flipkart_affiliate_id="dealsearch")


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session
    engine.dispose()


@pytest.fixture
def seeded(session, settings):
    ingest(session, SampleFeedConnector().fetch(), settings)
    return session


@pytest.fixture
def client(seeded):
    app.dependency_overrides[get_session] = lambda: seeded
    yield TestClient(app)
    app.dependency_overrides.clear()
