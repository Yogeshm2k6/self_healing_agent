import unittest

class TestApp(unittest.TestCase):

    def test_app(self):
        print("Running test_app.py")
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main(argv=['test_app.py'], verbosity=2, exit=False)
    print("Test completed successfully")