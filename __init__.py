
from .latus.test import test_latus

def setUpPackage():
    tl = test_latus.test_latus()
    tl.clean()
    tl.write_files()

def tearDownPackage():
    tl = test_latus.test_latus()
    # jca
    # todo: how do I control this?  at this point I have to edit this file ... :(
    if False:
        tl.clean()