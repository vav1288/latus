
import os

import latus


class CloudFolders:
    def __init__(self, cloud_root):
        self.__latus_cloud_folder = os.path.join(cloud_root, '.' + latus.__application_name__)

    @property
    def latus(self):
        return self.__latus_cloud_folder

    @property
    def cache(self):
        return os.path.join(self.__latus_cloud_folder, '.cache')

    @property
    def nodes(self):
        # file system database
        return os.path.join(self.__latus_cloud_folder, '.nodes')

