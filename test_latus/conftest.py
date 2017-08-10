
import pytest

import test_latus
import test_latus.tstutil
import latus.aws
import latus.aws.util.init_aws_db


@pytest.fixture(scope="session")
def session_setup():
    test_latus.tstutil.clean()


@pytest.fixture(scope="module")
def module_setup():
    cc = test_latus.tstutil.get_cloud_config()
    if cc['aws_local']:
        print('*** dropall ***')
        latus.aws.util.init_aws_db.aws_drop_all(latus.aws.dynamo_db_endpoint_url)
