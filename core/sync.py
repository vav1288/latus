
import os
import json
import pprint
import core.logger
import core.util
import core.const
import core.metadatapath
import core.walker
import core.hash
import core.compression

class Sync():
    """
    Determines what needs to be done to sync local to cloud.
    """
    DATABASE_FILE_NAME = '.' + core.const.NAME + '_sync_db' + '.json' # reserved
    def __init__(self, password, latus_folder, cloud_root, appdata_folder = None, verbose = False):
        self.password = password
        self.cloud_root = cloud_root
        self.latus_folder = latus_folder
        self.verbose = verbose
        if self.verbose:
            print('local_folder', self.latus_folder)
            print('cloud_root', self.cloud_root)
            print('cloud_folder', self.get_cloud_folder())

        core.util.make_dirs(self.latus_folder)

        if appdata_folder is None:
            # I'd like to use winpaths.get_local_appdata() but it doesn't seem to work with Python 3, so I'll
            # rely on the environment variable.
            self.appdata_folder = os.environ['APPDATA']

    def get_cloud_folder(self):
        return os.path.join(self.cloud_root, '.' + core.const.NAME)

    def sync(self):
        # check for new or updated local files
        local_walker = core.walker.Walker(self.latus_folder)
        for partial_path in local_walker:
            # this is where we use the local _file_ name to create the cloud _folder_ where the .zips and metadata reside
            full_path = local_walker.full_path(partial_path)
            file_as_cloud_folder = os.path.join(self.get_cloud_folder(), partial_path)
            if not os.path.exists(file_as_cloud_folder):
                os.makedirs(file_as_cloud_folder)
                if self.verbose:
                    print('new local', partial_path)
            hash, _ = core.hash.calc_sha512(full_path)
            if hash is not None:
                cloud_zip_file = os.path.join(file_as_cloud_folder, hash + '.zip')
                if not os.path.exists(cloud_zip_file):
                    if self.verbose:
                        print('writing', partial_path, '(', cloud_zip_file, ')')
                    compressor = core.compression.Compression(self.password, self.verbose)
                    # Input to archive program (7z) is relative to the latus folder.  Note that we have to explicitly
                    # give the full abs path of the archive itself since it's in a different folder.
                    compressor.compress(self.latus_folder, partial_path, os.path.abspath(cloud_zip_file))
                    mtime = os.path.getmtime(full_path)
                    size = os.path.getsize(full_path)
                    self.update_database(partial_path, file_as_cloud_folder, hash, mtime, size)

        # check for new or updated cloud files
        # todo: we're actually only interested in dirs here ... make Walker have a dirs only mode
        cloud_walker = core.walker.Walker(self.get_cloud_folder(), do_dirs=True)
        for partial_path in cloud_walker:
            full_path = cloud_walker.full_path(partial_path)
            if os.path.isdir(full_path):
                print('checking for new cloud files', 'full_path', full_path)
                file_as_cloud_folder = os.path.join(self.get_cloud_folder(), partial_path)
                db = self.read_database(file_as_cloud_folder)
                file_path = db['path']
                version = db['versions'][-1] # last entry in the list is most recent
                hash = version['hash']
                # todo: compare hashes
                dest_path = os.path.join(self.latus_folder, file_path)
                if not os.path.exists(dest_path):
                    print('extracting', dest_path)
                    extractor = core.compression.Compression(self.password, self.verbose)
                    cloud_zip_file = os.path.join(file_as_cloud_folder, hash + '.zip')
                    extractor.expand(self.latus_folder, os.path.abspath(cloud_zip_file))

    def update_database(self, partial_path, file_as_cloud_folder, hash, mtime, size):
        db_file_path = os.path.join(file_as_cloud_folder, self.DATABASE_FILE_NAME)
        if os.path.exists(db_file_path):
            with open(db_file_path) as f:
                db_info = json.load(f)
        else:
            db_info = {'path' : partial_path, 'versions' : []}
        info = {'size' : size, 'hash' : hash, 'mtime' : mtime}
        db_info['versions'].append(info)
        with open(db_file_path, 'w') as f:
            json.dump(db_info, f, indent = 4)

    def read_database(self, file_as_cloud_folder):
        db_file_path = os.path.join(file_as_cloud_folder, self.DATABASE_FILE_NAME)
        with open(db_file_path) as f:
            db = json.load(f)
        return db