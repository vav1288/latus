
import boto3
import botocore.vendored.requests.exceptions
import botocore.exceptions

from latus import aws
from latus import logger


class TableBase:
    def __init__(self, table_name):
        self.table_name = table_name
        self.provisioned_throughput = {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}

        # derived classes provide these
        self.key_schema = None
        self.attribute_definitions = None

        logger.log.info('dynamo_db_endpoint_url : %s' % aws.dynamo_db_endpoint_url)
        logger.log.info('s3_endpoint_url : %s' % aws.s3_endpoint_url)

    def create_table(self):
        created_ok = False
        resource = aws.get_db_resource()
        client = aws.get_db_client()
        tables = client.list_tables()
        logger.log.info('tables : %s' % str(tables))
        if self.table_name not in tables['TableNames']:
            r = None
            try:
                r = resource.create_table(TableName=self.table_name, KeySchema=self.key_schema,
                                          AttributeDefinitions=self.attribute_definitions,
                                          ProvisionedThroughput=self.provisioned_throughput)
            except botocore.vendored.requests.exceptions.ConnectionError:
                logger.log.warn('create_table "%s" : connection error' % self.table_name)
            except botocore.exceptions.ClientError as e:
                logger.log.warn(str(e))
            else:
                created_ok = True
            logger.log.debug('create_table : %s : %s' % (self.table_name, str(r)))
        else:
            logger.log.debug('%s already exists' % self.table_name)
        return created_ok

    def delete_table(self):
        client = boto3.client('dynamodb')
        delete_ok = False
        try:
            tables = client.list_tables()
        except botocore.vendored.requests.exceptions.ConnectionError:
            logger.log.debug('delete_table "%s" : connection error' % self.table_name)
            tables = None
        else:
            delete_ok = True
        if tables and self.table_name in tables['TableNames']:
            client.delete_table(TableName=self.table_name)
        logger.log.debug('delete_table : %s : %s' % (self.table_name, delete_ok))
        return delete_ok

    def get_table_resource(self):
        resource = aws.get_db_resource()
        return resource.Table(self.table_name)

    def put(self, item):
        table = self.get_table_resource()
        put_ok = False
        try:
            table.put_item(Item=item)
        except botocore.vendored.requests.exceptions.ConnectionError:
            logger.log.error('put_item : table="%s" item="%s" : connection error' % (self.table_name, str(item)))
        except botocore.exceptions.ClientError as e:
            self.create_table()
            put_ok = self.put(item)
        else:
            put_ok = True
        logger.log.debug('put_ok : %s : %s' % (put_ok, item))
        return put_ok

    def get_all(self):
        client = aws.get_db_client()
        paginator = client.get_paginator('scan')
        items = []
        try:
            for page in paginator.paginate(TableName=self.table_name):
                items.extend(page['Items'])
        except botocore.exceptions.ClientError as e:
            self.create_table()
            items = self.get_all()
        return items
