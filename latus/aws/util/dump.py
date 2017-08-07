
import boto3
from pprint import pprint


def dump_all(db_endpoint_url, s3_endpoint_url):
    db_client = boto3.client('dynamodb', endpoint_url=db_endpoint_url)
    s3_client = boto3.client('s3', endpoint_url=s3_endpoint_url)
    s3_resource = boto3.resource('s3', endpoint_url=s3_endpoint_url)

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

