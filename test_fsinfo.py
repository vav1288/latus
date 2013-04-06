
import fsinfo
import const

def test_fsinfo():
    info = fsinfo.fsinfo(const.TEST_DIR)
    info.run()
