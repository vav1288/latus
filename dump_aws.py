
from latus.aws.util.dump import dump_all
from latus.aws.util.urls import get_local_aws_db_url, get_local_aws_s3_url

if __name__ == '__main__':
    dump_all(get_local_aws_db_url(), get_local_aws_s3_url())
