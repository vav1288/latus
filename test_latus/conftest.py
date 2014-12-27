
import logging
import pytest
import latus.logger
import test_latus.create_files

nodynamicdatadelete = None # keep data around

def pytest_addoption(parser):
    parser.addoption("--nodynamicdatadelete", action="store_true", default=False,
        help="keep the dynamically created data around after the test")

def pytest_generate_tests(metafunc):
    global nodynamicdatadelete
    nodynamicdatadelete = metafunc.config.getoption('nodynamicdatadelete')

@pytest.fixture(scope="module")
def setup(request):

    def clean():
        global nodynamicdatadelete
        if nodynamicdatadelete is False:
            test_latus.create_files.clean()

    latus.logger.init()
    latus.logger.set_console_log_level(logging.INFO)
    latus.logger.set_file_log_level(logging.DEBUG)
    latus.logger.log.info("nodynamicdatadelete:" + str(nodynamicdatadelete))
    t = test_latus.create_files.TestFiles()
    test_latus.create_files.clean()
    t.write_files()

    request.addfinalizer(clean)
    return t