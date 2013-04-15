
import time
import os
import unittest
from . import test_latus
from .. import propmtime

class test_propmtime(unittest.TestCase):
    def test_propmtime(self):
        pmt = propmtime.propmtime(test_latus.get_mtime_root(), print_flag=True)
        mtime = pmt.run()
        print((time.asctime(time.gmtime(mtime))))
        self.assertEqual(os.path.getmtime(test_latus.get_mtime_root()), test_latus.get_mtime_time())

if __name__ == "__main__":
    unittest.main()