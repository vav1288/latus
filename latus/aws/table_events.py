
from latus.aws import table_base

from latus import logger


class TableEvents(table_base.TableBase):
    def __init__(self, aws_local):
        super().__init__('fsevents', aws_local)

        self.key_schema = [{'AttributeName': 'originator', 'KeyType': 'HASH'},  # Partition key
                           {'AttributeName': 'mivui', 'KeyType': 'RANGE'}]  # Sort key
        self.attribute_definitions = [{'AttributeName': 'originator', 'AttributeType': 'S'},
                                      {'AttributeName': 'mivui', 'AttributeType': 'N'}]

    def add(self, mivui, originator, event_type, detection, file_path, src_path, size, file_hash, mtime):
        if mtime:
            mtime = mtime.isoformat()
        info = {'mivui': mivui, "originator": originator, 'event_type': event_type, 'detection': detection,
                'file_path': file_path, 'src_path': src_path, 'size': size, 'file_hash': file_hash,
                'mtime': mtime}
        logger.log.info('TableEvents add : %s' % info)
        return self.put(info)
