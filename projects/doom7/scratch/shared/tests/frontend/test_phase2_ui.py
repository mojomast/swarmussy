import unittest
import os

class TestPhase2UI(unittest.TestCase):
    def test_phase2_files_exist_and_nonempty(self):
        files = [
            "shared/frontend/phase2/Phase2Flow.jsx",
            "shared/frontend/phase2/Phase2Dashboard.jsx",
        ]
        for f in files:
            self.assertTrue(os.path.exists(f), f"{f} should exist")
            self.assertTrue(os.path.getsize(f) > 0, f"{f} should not be empty")

if __name__ == '__main__':
    unittest.main()
