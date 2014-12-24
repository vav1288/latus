
import logging
import pytest
import latus.logger
import test.create_files

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
            test.create_files.clean(do_all=False)

    latus.logger.set_log_level(logging.INFO)
    latus.logger.log.info("nodynamicdatadelete:" + str(nodynamicdatadelete))
    t = test.create_files.TestFiles()
    test.create_files.clean(do_all=True)
    t.write_files()

    request.addfinalizer(clean)
    return t