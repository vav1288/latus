
from pprint import pprint

import latus.aws.aws_access


def dump_all(aws_local):

    access_aws = latus.aws.aws_access.AWSAccess(aws_local)
    db_client = access_aws.get_db_client()
    s3_client = access_aws.get_s3_client()
    s3_resource = access_aws.get_s3_resource()

    buckets = s3_client.list_buckets()['Buckets']
    print('Buckets:')
    pprint(buckets)
    for bucket in buckets:
        bucket_resource = s3_resource.Bucket(bucket['Name'])
        for bucket_object in bucket_resource.objects.all():
            print(bucket_object)

    print()

    tables = db_client.list_tables()['TableNames']
    print('Tables : %s' % tables)
    for table in tables:
        paginator = db_client.get_paginator('scan')
        items = []
        for page in paginator.paginate(TableName=table):
            items.extend(page['Items'])
        print('Table : %s' % table)
        pprint(items)
        print()

