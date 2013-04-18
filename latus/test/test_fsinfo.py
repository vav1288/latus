from .. import fsinfo
from . import test_latus


def test_fsinfo():
    info = fsinfo.fsinfo(test_latus.get_root())
    info.run()

if __name__ == "__main__":
    test_fsinfo()