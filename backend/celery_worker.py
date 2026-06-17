from app import create_app
from app.extensions import celery
import app.services.importer  # noqa: F401 — registers Celery tasks

flask_app = create_app()
