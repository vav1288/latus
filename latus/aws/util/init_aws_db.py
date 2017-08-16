
import boto3

from latus.aws.aws_access import AWSAccess


def aws_drop_all():
    aws = AWSAccess(True)
    client = aws.get_db_client()
    tables = client.list_tables()['TableNames']
    for table in tables:
        client.delete_table(TableName=table)


if __name__ == '__main__':
    aws_drop_all()
