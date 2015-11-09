
import pytest
import test_latus.util


@pytest.fixture(scope="session")
def setup():
    test_latus.util.clean()
