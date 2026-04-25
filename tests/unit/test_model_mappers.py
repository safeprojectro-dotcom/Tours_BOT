"""Y36.2A: ensure SQLAlchemy mappers configure (catches missing back_populates on User)."""

import unittest

from sqlalchemy.orm import configure_mappers


class TestModelMappers(unittest.TestCase):
    def test_configure_mappers_succeeds(self) -> None:
        import app.models  # noqa: F401 — register all ORM models

        configure_mappers()
