
import pytest
import test_latus.tstutil


@pytest.fixture(scope="session")
def setup():
    test_latus.tstutil.clean()
