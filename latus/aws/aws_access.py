import os

import boto3
from botocore.exceptions import ClientError

import latus
from latus import logger
from latus.aws.table_events import TableEvents
from latus.aws.table_node import TableNodes


class AWSAccess:
    def __init__(self, aws_local):
        if aws_local:
            # pick one of these
            dynamo_db_localstack_port = "4569"  # https://github.com/localstack/localstack
            dynamo_db_local_port = "8000"  # http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html
            self.dynamo_db_endpoint_url = "http://localhost:%s" % dynamo_db_localstack_port

            s3_localstack_port = "4572"
            self.s3_endpoint_url = "http://localhost:%s" % s3_localstack_port

            sns_localstack_port = "4575"
            self.sns_endpoint_url = "http://localhost:%s" % sns_localstack_port

            sqs_localstack_port = "4576"
            self.sqs_enpoint_url = "http://localhost:%s" % sqs_localstack_port
        else:
            # regular AWS
            self.dynamo_db_endpoint_url = None
            self.s3_endpoint_url = None
            self.sns_endpoint_url = None
            self.sqs_endpoint_url = None

    def get_db_client(self):
        return boto3.client('dynamodb', endpoint_url=self.dynamo_db_endpoint_url)

    def get_db_resource(self):
        return boto3.resource('dynamodb', endpoint_url=self.dynamo_db_endpoint_url)

    def get_s3_client(self):
        return boto3.client('s3', endpoint_url=self.s3_endpoint_url)

    def get_s3_resource(self):
        return boto3.resource('s3', endpoint_url=self.s3_endpoint_url)

    def get_sns_client(self):
        return boto3.client('sns', endpoint_url=self.sns_endpoint_url)

    def get_sns_resource(self):
        return boto3.resource('sns', endpoint_url=self.sns_endpoint_url)

    def get_sqs_client(self):
        return boto3.client('sqs', endpoint_url=self.sqs_endpoint_url)

    def get_sqs_resource(self):
        return boto3.resource('sqs', endpoint_url=self.sqs_endpoint_url)

    def get_all_tables(self):
        return self.get_db_client().list_tables()['TableNames']


class LatusS3:
    def __init__(self, pref, aws_local):
        self.latus_storage_bucket_name = '%s%s' % (latus.__application_name__, 'storage')
        aws_access = AWSAccess(aws_local)
        self.s3_client = aws_access.get_s3_client()
        self.s3_resource = aws_access.get_s3_resource()

        # create bucket (OK if it already exists - if it already exists S3 does nothing)
        # http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region
        if aws_local:
            self.s3_client.create_bucket(Bucket=self.latus_storage_bucket_name,
                                         CreateBucketConfiguration={'LocationConstraint': 'us-east-1'})
        else:
            aws_location = pref.get_aws_location()
            if aws_location:
                try:
                    self.s3_client.create_bucket(Bucket=self.latus_storage_bucket_name,
                                                 CreateBucketConfiguration={'LocationConstraint': aws_location})
                except ClientError as e:
                    logger.log.warn(str(e))
            else:
                logger.log.warn('no AWS location set')

    def upload_file(self, file_path, hash):
        # upload file to S3 if it's not already there
        # todo: test if already in S3
        logger.log.info('upload_file : file_path=%s, hash=%s' % (file_path, hash))
        self.s3_resource.Bucket(self.latus_storage_bucket_name).upload_file(file_path, hash)

    def download_file(self, file_path, key):
        logger.log.info('download_file : file_path=%s, key=%s' % (file_path, key))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self.s3_resource.Bucket(self.latus_storage_bucket_name).download_file(key, file_path)


def init(aws_local):
    aws = AWSAccess(aws_local)
    for table in [TableEvents(aws_local), TableNodes(aws_local)]:
        if table.table_name not in aws.get_all_tables():
            table.create_table()


def drop_all(aws_local):
    aws = AWSAccess(aws_local)
    resource = aws.get_db_resource()
    for table_name in aws.get_all_tables():
        logger.log.info('deleting %s' % table_name)
        resource.Table(table_name).delete()

