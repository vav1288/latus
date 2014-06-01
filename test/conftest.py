
import pytest
import test.create_files

nodynamicdatadelete = False # keep data around

def pytest_addoption(parser):
    parser.addoption("--nodynamicdatadelete", action="store_true", default=False,
        help="keep the dynamically created data around after the test")

def pytest_generate_tests(metafunc):
    if 'nodynamicdatadelete' in metafunc.fixturenames:
        global nodynamicdatadelete
        nodynamicdatadelete = True


@pytest.fixture(scope="module")
def setup(request):

    def clean():
        global nodynamicdatadelete
        if nodynamicdatadelete is False:
            test.create_files.clean(all=False)

    t = test.create_files.TestFiles()
    test.create_files.clean()
    t.write_files()

    request.addfinalizer(clean)
    return t  # provide the fixture value