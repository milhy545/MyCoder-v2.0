import unittest
import os
import shutil
from src.utils.file_ops import read_file, write_file

class TestFileOps(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_write_and_read_file(self):
        file_path = os.path.join(self.test_dir, "test.txt")
        content = "Hello, World!"

        # Test write
        write_file(file_path, content)
        self.assertTrue(os.path.exists(file_path))

        # Test read
        read_content = read_file(file_path)
        self.assertEqual(read_content, content)

    def test_read_non_existent_file(self):
        file_path = os.path.join(self.test_dir, "non_existent.txt")
        with self.assertRaises(FileNotFoundError):
            read_file(file_path)

    def test_write_to_invalid_path(self):
        # Trying to write to a directory path instead of a file
        # Note: writing to a directory usually raises IsADirectoryError which inherits from IOError (OSError)
        file_path = self.test_dir
        with self.assertRaises(IOError):
            write_file(file_path, "content")

if __name__ == '__main__':
    unittest.main()
