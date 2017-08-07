

def get_local_aws_db_url():

    # pick one of these
    localstack_port = "4569"
    dynamo_db_local_port = "8000"
    url = "http://localhost:%s" % localstack_port

    print(url)
    return url


def get_local_aws_s3_url():

    localstack_port = "4572"
    url = "http://localhost:%s" % localstack_port

    print(url)
    return url


