
from latus import logger

import latus.aws.util.aws_util


def main():
    logger.init('temp')
    # todo: make local vs. real AWS a parameter, but for now it's localstack
    print('dumping localstack')
    latus.aws.util.aws_util.dump_all(True)

if __name__ == '__main__':
    main()
