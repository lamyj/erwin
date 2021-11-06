import subprocess
import sys
import unittest

import erwin.__main__

class TestMain(unittest.TestCase):
    def test_help(self):
        output = subprocess.check_output(
            [sys.executable, "-m", "erwin", "--help"])
    
    def test_list(self):
        output = subprocess.check_output(
            [sys.executable, "-m", "erwin", "--list"])

if __name__ == "__main__":
    unittest.main()
