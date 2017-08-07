
import boto3

from latus.aws.util.urls import get_local_aws_db_url


def aws_drop_all(endpoint_url):
    client = boto3.client('dynamodb', endpoint_url=endpoint_url)
    tables = client.list_tables()['TableNames']
    for table in tables:
        client.delete_table(TableName=table)


if __name__ == '__main__':
    aws_drop_all(get_local_aws_db_url())
