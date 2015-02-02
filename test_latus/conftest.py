
import pytest
import test_latus.create_files


@pytest.fixture(scope="session")
def setup():
    test_latus.create_files.clean()
