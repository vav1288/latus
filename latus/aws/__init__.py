
import os

import boto3
from botocore.client import ClientError

import latus
from latus import logger
from latus.aws.table_events import TableEvents
from latus.aws.table_node import TableNodes

# default is regular AWS
dynamo_db_endpoint_url = None
s3_endpoint_url = None
sns_endpoint_url = None
sqs_endpoint_url = None

latus_storage_bucket_name = '%s%s' % (latus.__application_name__, 'storage')


def init():
    for table in [TableEvents(), TableNodes()]:
        if table.table_name not in get_all_tables():
            table.create_table()


def local_testing():
    global dynamo_db_endpoint_url, s3_endpoint_url, sns_endpoint_url, sqs_endpoint_url
    if logger.log:
        logger.log.info('setting AWS for local testing')

    # pick one of these
    dynamo_db_localstack_port = "4569"  # https://github.com/localstack/localstack
    dynamo_db_local_port = "8000"  # http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html
    dynamo_db_endpoint_url = "http://localhost:%s" % dynamo_db_localstack_port

    s3_localstack_port = "4572"
    s3_endpoint_url = "http://localhost:%s" % s3_localstack_port

    sns_localstack_port = "4575"
    sns_endpoint_url = "http://localhost:%s" % sns_localstack_port

    sqs_localstack_port = "4576"
    sqs_enpoint_url = "http://localhost:%s" % sqs_localstack_port

    if logger.log:
        logger.log.info('AWS dynamo_db_endpoint_url : "%s"' % dynamo_db_endpoint_url)
        logger.log.info('AWS s3_db_endpoint_url : "%s"' % s3_endpoint_url)
        logger.log.info('AWS sns_endpoint_url : "%s"' % sns_endpoint_url)
        logger.log.info('AWS sqs_enpoint_url : "%s"' % sqs_enpoint_url)


def get_db_client():
    return boto3.client('dynamodb', endpoint_url=dynamo_db_endpoint_url)


def get_db_resource():
    return boto3.resource('dynamodb', endpoint_url=dynamo_db_endpoint_url)


def get_s3_client():
    return boto3.client('s3', endpoint_url=s3_endpoint_url)


def get_s3_resource():
    return boto3.resource('s3', endpoint_url=s3_endpoint_url)


def get_sns_client():
    return boto3.client('sns', endpoint_url=sns_endpoint_url)


def get_sns_resource():
    return boto3.resource('sns', endpoint_url=sns_endpoint_url)


def get_sqs_client():
    return boto3.client('sqs', endpoint_url=sqs_endpoint_url)


def get_sqs_resource():
    return boto3.resource('sqs', endpoint_url=sqs_endpoint_url)


def get_all_tables():
    return get_db_client().list_tables()['TableNames']


def drop_all():
    resource = get_db_resource()
    for table_name in get_all_tables():
        logger.log.info('deleting %s' % table_name)
        resource.Table(table_name).delete()


class LatusS3:
    def __init__(self, pref):
        self.s3_client = get_s3_client()
        self.s3_resource = get_s3_resource()
        self.is_local = pref.get_aws_local()

        # create bucket (OK if it already exists - if it already exists S3 does nothing)
        # http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region
        if self.is_local:
            self.s3_client.create_bucket(Bucket=latus_storage_bucket_name)
        else:
            try:
                self.s3_client.create_bucket(Bucket=latus_storage_bucket_name,
                                            CreateBucketConfiguration={'LocationConstraint': pref.get_aws_location()})
            except ClientError as e:
                logger.log.warn(str(e))

    def upload_file(self, file_path, hash):
        # upload file to S3 if it's not already there
        # todo: test if already in S3
        logger.log.info('upload_file : file_path=%s, hash=%s' % (file_path, hash))
        self.s3_resource.Bucket(latus_storage_bucket_name).upload_file(file_path, hash)

    def download_file(self, file_path, key):
        logger.log.info('download_file : file_path=%s, key=%s' % (file_path, key))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self.s3_resource.Bucket(latus_storage_bucket_name).download_file(key, file_path)
