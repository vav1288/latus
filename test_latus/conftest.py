
import pytest

import test_latus
import test_latus.tstutil
import latus.aws
import latus.aws.util.init_aws_db
import latus.logger


@pytest.fixture(scope="session")
def session_setup():
    test_latus.tstutil.clean()


@pytest.fixture(scope="module")
def module_setup():
    cc = test_latus.tstutil.get_cloud_config()
    if cc['aws_local']:
        latus.aws.local_testing()
        print('*** dropall ***', latus.aws.dynamo_db_endpoint_url)
        if latus.logger.log:
            latus.logger.log.warn('*** dropall ***')
        latus.aws.util.init_aws_db.aws_drop_all(latus.aws.dynamo_db_endpoint_url)
