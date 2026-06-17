import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import routers.main as main
import seed_db


class TestSeedDB(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        main.engine = self.engine
        main.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        main.Base.metadata.create_all(bind=self.engine)

    def test_seed_creates_rooms(self):
        seed_db.seed()
        session = main.SessionLocal()
        rooms = session.query(main.Room).all()
        self.assertEqual(len(rooms), 4)
        names = [room.name for room in rooms]
        self.assertIn("Deluxe Ocean View", names)
        self.assertIn("Penthouse", names)
        session.close()

    def test_seed_idempotent(self):
        seed_db.seed()
        session = main.SessionLocal()
        first_count = session.query(main.Room).count()
        session.close()

        seed_db.seed()

        session = main.SessionLocal()
        second_count = session.query(main.Room).count()
        session.close()
        self.assertEqual(first_count, second_count)
