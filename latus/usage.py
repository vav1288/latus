
import platform
import getpass
import appdirs
import shutil
import os
import logging
import hashlib
import binascii

import requests

import latus
import latus.const
import latus.logger
import latus.preferences
import latus.nodedb
import latus.util
import latus.folders

def anonymize(s):
    m = hashlib.sha256()
    m.update(s.encode())
    return str(binascii.hexlify(m.digest()))

def get_folder_size(root):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(root):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def get_info_from_folder(name, folder_path):
    info = {}
    folder_usage = shutil.disk_usage(folder_path)
    info[name + 'folder'] = folder_path
    info[name + 'disktotal'] = folder_usage[0]
    info[name + 'diskused'] = folder_usage[1]
    info[name + 'used'] = get_folder_size(folder_path)
    return info


class LatusUsageInfo:
    def __init__(self, latus_config_folder):
        self.latus_config_folder = latus_config_folder

    def __iter__(self):
        yield ('ip', None, None)  # special case - the server side provides the IP address
        pref = latus.preferences.Preferences(self.latus_config_folder)

        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        self.node_db = latus.nodedb.NodeDB(cloud_folders.nodes, pref.get_node_id())
        for latus_folder in latus.util.get_latus_folders(pref):
            yield ('folderpref', anonymize(latus_folder), str(self.node_db.get_folder_preferences_from_folder(latus_folder)))

        for n, d in [('c', pref.get_cloud_root()), ('l', pref.get_latus_folder())]:
            infos = get_info_from_folder(n, d)
            for info in infos:
                yield (info, None, infos[info])

        yield ('username', None, anonymize(getpass.getuser()))
        yield ('computername', None, anonymize(platform.node()))
        yield ('version', None, latus.__version__)
        yield ('preferencesdbversion', None, latus.preferences.__db_version__)
        yield ('nodedbversion', None, latus.nodedb.__db_version__)


def upload_usage_info():
    latus_config_folder = appdirs.user_config_dir(latus.const.NAME, latus.const.COMPANY)
    preferences = latus.preferences.Preferences(latus_config_folder)
    usage_info = LatusUsageInfo(latus_config_folder)
    for k,n,v in usage_info:
        info = {'app': latus.const.NAME, 'id': preferences.get_node_id(), 'k': k, 'n': n, 'v': v}
        r = requests.post(latus.const.USAGE_API_URL, json=info)
        latus.logger.log.info(r.text)
        if r.status_code != 200:
            latus.logger.log.error('%s failed with %s status' % (latus.const.USAGE_API_URL, str(r.status_code)))
            break


def main():
    latus.logger.init(os.path.join('temp', 'latus_usage'))
    latus.logger.set_console_log_level(logging.INFO)
    upload_usage_info()

if __name__ == '__main__':
    main()
