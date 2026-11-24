import tempfile
import unittest
from pathlib import Path
from core.database import Database

class DatabaseTests(unittest.TestCase):
    def test_conversation_and_message_persist(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "test.db")
            db.initialize()
            conversation_id = db.create_conversation("astra", "Test")
            db.add_message(conversation_id, "user", "Hello")
            conversations = db.list_conversations("astra")
            self.assertEqual(len(conversations), 1)
            self.assertEqual(conversations[0]["title"], "Test")

if __name__ == "__main__":
    unittest.main()
