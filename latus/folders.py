
import os
import pathlib

import latus.const


class CloudFolders:
    def __init__(self, cloud_root):
        self.__latus_cloud_folder = os.path.join(cloud_root, '.' + latus.const.NAME)

    @property
    def latus(self):
        return self.__latus_cloud_folder

    @property
    def cache(self):
        return os.path.join(self.__latus_cloud_folder, 'cache')

    @property
    def nodes(self):
        # file system database
        return os.path.join(self.__latus_cloud_folder, 'nodes')


def latus_cloud_folder_from_latus_folder(path):
    return os.path.join(path, latus.const.LATUS_CLOUD)


def is_latus_cloud_folder(path):
    # e.g. if path is latus/cloud/< something >
    parts = pathlib.Path(path).parts
    if len(parts) >= 2:
        return parts[0] == latus.const.NAME and parts[1] == latus.const.LATUS_CLOUD
    return False
