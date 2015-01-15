
import logging
import pytest
import latus.logger
import test_latus.create_files


def init():
    latus.logger.init()
    latus.logger.set_console_log_level(logging.INFO)
    latus.logger.set_file_log_level(logging.DEBUG)


@pytest.fixture(scope="module")
def setup(request):
    init()

