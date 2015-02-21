
import os

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
    def fsdb(self):
        # file system database
        return os.path.join(self.__latus_cloud_folder, 'fsdb')

    @property
    def miv(self):
        # monotonically increasing value
        return os.path.join(self.__latus_cloud_folder, 'miv')

    @property
    def comm(self):
        # LAN communications
        return os.path.join(self.__latus_cloud_folder, 'comm')