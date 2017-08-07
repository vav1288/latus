
import pytest

import test_latus
import test_latus.tstutil
import latus.aws
import latus.aws.util.init_aws_db


@pytest.fixture(scope="session")
def session_setup():
    # todo: make this a py.test parameter?
    test_latus.cloud_storage_mode = 'aws'  # 'aws' or 'csp'
    test_latus.tstutil.clean()


@pytest.fixture(scope="module")
def module_setup():
    # for pytest we only use local testing (since it potentially costs money for the real AWS)
    latus.aws.local_testing()
    assert(latus.aws.dynamo_db_endpoint_url is not None)
    assert('localhost' in latus.aws.dynamo_db_endpoint_url)
    if 'localhost' in latus.aws.dynamo_db_endpoint_url:
        latus.aws.util.init_aws_db.aws_drop_all(latus.aws.dynamo_db_endpoint_url)
