
from .. import fsinfo
from .. import const

def test_fsinfo():
    info = fsinfo.fsinfo(const.TEST_DIR)
    info.run()

if __name__ == "__main__":
    test_fsinfo()