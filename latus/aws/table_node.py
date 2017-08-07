
import os
import platform
import datetime

from boto3.dynamodb.conditions import Key

from latus.aws import table_base
from latus import logger


class TableNodes(table_base.TableBase):
    def __init__(self):
        super().__init__('nodes')
        self.key_schema = [{'AttributeName': 'nodeid', 'KeyType': 'HASH'}]
        self.attribute_definitions = [{'AttributeName': 'nodeid', 'AttributeType': 'S'}]

    def register(self, node_id):
        table_resource = self.get_table_resource()
        response = table_resource.query(KeyConditionExpression=Key('nodeid').eq(node_id))
        entries = response['Items']
        now = datetime.datetime.utcnow().isoformat()
        computer_name = platform.node()
        user_name = os.getlogin()
        if len(entries) < 1:
            self.put({'nodeid': node_id,
                      'created_dt': now, 'created_user': user_name, 'created_computer_name': computer_name,
                      'most_recent_dt': now, 'most_recent_user': user_name, 'most_recent_computer_name': computer_name
                      })
            created_flag = True
            logger.log.info('registering node_id "%s"' % node_id)
        else:
            logger.log.info('node_id "%s" already registered - updating' % node_id)
            response = table_resource.update_item(
                Key={'nodeid': node_id},
                UpdateExpression="set most_recent_dt = :d, most_recent_user = :u, most_recent_computer_name = :c",
                ExpressionAttributeValues={
                    ':d': now,
                    ':u': user_name,
                    ':c': computer_name
                },
                ReturnValues="ALL_NEW"
            )
            logger.log.info(str(response['Attributes']))
            created_flag = False
        return created_flag

    def get_all_nodes(self):
        all_nodes = None
        table_resource = self.get_table_resource()
        if table_resource:
            response = table_resource.scan()
            if response:
                all_nodes = sorted([e['nodeid'] for e in response['Items']])
        logger.log.info('all nodes : %s' % str(all_nodes))
        return all_nodes
