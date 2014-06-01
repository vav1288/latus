
"""
Spans the entire testing session.
"""

import pytest
import test.test_files

@pytest.fixture(scope="session")
def test_set_up():
    test_files = test.test_files.TestFiles()
    test_files.clean()
    test_files.write_files()

@pytest.fixture(scope="session")
def test_tear_down():
    test_files = test.test_files.TestFiles()
    # todo: how do I control this?  at this point I have to edit this file ... :(
    if False:
        test_files.clean()