
import os
import datetime
import threading
import logging
import glob

from simplecrypto import RsaKeypair, RsaPublicKey

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

import watchdog.observers
import watchdog.events

import latus.const
import latus.nodedb
import latus.preferences
import latus.folders
import latus.logger
import latus.util
import latus.crypto

KEY_MANAGEMENT_FILE = 'keys' + latus.const.DB_EXTENSION

Base = sqlalchemy.ext.declarative.declarative_base()

g_is_gui = False  # True = GUI, False = CLI
g_allow_always = False  # set to True to not ask for permission to provide crypto key (for testing purposes only)


def session_maker(app_data_folder):
    pref = latus.preferences.Preferences(app_data_folder)
    cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
    if not os.path.exists(cloud_folders.keys):
        os.mkdir(cloud_folders.keys)
    sqlite_path = 'sqlite:///' + os.path.abspath(os.path.join(cloud_folders.keys, KEY_MANAGEMENT_FILE))
    db_engine = sqlalchemy.create_engine(sqlite_path)  # , echo=True)
    session = sqlalchemy.orm.sessionmaker(bind=db_engine)
    Base.metadata.create_all(db_engine)
    return session


class KeyManagementTable(Base):
    __tablename__ = 'keys'

    index = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    source = sqlalchemy.Column(sqlalchemy.String())
    destination = sqlalchemy.Column(sqlalchemy.String())
    encrypted_latus_key = sqlalchemy.Column(sqlalchemy.String())
    datetime = sqlalchemy.Column(sqlalchemy.DateTime())


class KeyRequestTable(Base):
    __tablename__ = 'requests'

    requester = sqlalchemy.Column(sqlalchemy.String(), primary_key=True)
    datetime = sqlalchemy.Column(sqlalchemy.DateTime())


class DBUpdateHandler(watchdog.events.FileSystemEventHandler):

    def __init__(self, app_data_folder):
        self.app_data_folder = app_data_folder
        super().__init__()

    def dispatch(self, event):
        if os.path.basename(event.src_path) == KEY_MANAGEMENT_FILE:
            pref = latus.preferences.Preferences(self.app_data_folder)
            cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
            this_node_id = pref.get_node_id()
            latus.logger.log.info('dispatch src_path : %s : %s' % (this_node_id, str(event.src_path)))
            session = session_maker(self.app_data_folder)
            s = session()

            # if we don't have a key, get or create one
            if not pref.get_crypto_key():
                latus_keys = set()
                sources = set()
                latus.logger.log.info('%s : looking for key' % this_node_id)
                for row in s.query(KeyManagementTable).filter_by(destination=this_node_id):
                    private_key = RsaKeypair(pref.get_private_key())
                    latus_key = private_key.decrypt(row.encrypted_latus_key)
                    if latus_key not in latus_keys:
                        latus_keys.add(latus_key)
                        sources.add(row.source)
                if len(latus_keys) > 0:
                    latus.logger.log.info('%s : got latus key from %s' % (this_node_id, str(sources)))
                    pref.set_crypto_key(min(latus_keys))  # if more than one, take the first one in order
                else:
                    latus.logger.log.info('%s : no key found' % this_node_id)
                if not pref.get_crypto_key():
                    other_nodes = set()
                    for db_file_path in glob.glob(os.path.join(cloud_folders.nodedb, '*' + latus.const.DB_EXTENSION)):
                        file_name = os.path.basename(db_file_path)
                        node_id = file_name.split('.')[0]
                        if node_id != this_node_id:
                            other_nodes.add(node_id)
                    latus.logger.log.info('%s : other_nodes = %s' % (this_node_id, str(other_nodes)))
                    if len(other_nodes) < 1:
                        latus.logger.log.info('%s : creating new latus key' % this_node_id)
                        pref.set_crypto_key(latus.crypto.new_key())

            # respond to key requests
            for row in s.query(KeyRequestTable):
                if row.requester != this_node_id:
                    # got a key request (from someone other than ourselves)
                    r = s.query(KeyManagementTable).filter_by(destination=row.requester).first()
                    if not r:
                        # no one else has responded, so we will
                        requester_node_db = latus.nodedb.NodeDB(cloud_folders.nodedb, row.requester)
                        if get_permission(requester_node_db.get_user(), requester_node_db.get_computer()):
                            latus.logger.log.info('%s : answering key request from %s' % (this_node_id, row.requester))

                            # give the requester the key (encrypted, of course)
                            requester_public_key = RsaPublicKey(requester_node_db.get_public_key())
                            crypto_key = pref.get_crypto_key()
                            if crypto_key:
                                encrypted_latus_key = requester_public_key.encrypt(crypto_key)
                                kmt = KeyManagementTable(source=this_node_id, destination=row.requester,
                                                         encrypted_latus_key=encrypted_latus_key,
                                                         datetime=datetime.datetime.utcnow())
                                q = s.query(KeyManagementTable).filter_by(source=this_node_id).filter_by(destination=row.requester).first()
                                if q:
                                    s.delete(q)
                                s.add(kmt)
                                s.commit()
                            else:
                                latus.logger.log.error('%s : no crypto key' % this_node_id)
                        else:
                            latus.logger.log.warn('%s : denied request from %s' % (this_node_id, row.requester))
            s.close()
        return


def get_permission(user, computer):
    if g_allow_always:
        latus.logger.log.info('always allowing key permission (OK for testing)')
        return True
    msg = '"' + user + '" is asking for latus key permission from "' + computer
    msg += '".  Would you like to grant permission?'
    if g_is_gui:
        gui_msg = msg + '\n\nIf you do not recognize this request click "No".'
        from PyQt5 import QtWidgets
        app = QtWidgets.QApplication([])  # need 'app' to remain active (in scope) for message box to work
        reply = QtWidgets.QMessageBox.question(QtWidgets.QMessageBox(), 'Key Permission', gui_msg,
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        return reply == QtWidgets.QMessageBox.Yes
    else:
        cli_msg = msg + '(y/n)'
        reply = input(cli_msg).lower()
        return 'y' in reply


class KeyManagement(threading.Thread):

    def __init__(self, app_data_folder, is_gui, allow_always=False):
        self.app_data_folder = app_data_folder
        global g_is_gui, g_allow_always
        g_is_gui = is_gui
        g_allow_always = allow_always

        self.observer = watchdog.observers.Observer()
        self.handler = None

        # creates the DB if it doesn't already exist
        session = session_maker(self.app_data_folder)
        s = session()
        s.commit()
        s.close()

        super().__init__()

    def run(self):
        pref = latus.preferences.Preferences(self.app_data_folder)
        latus.logger.log.info('starting key management : %s' % pref.get_node_id())
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())

        self.handler = DBUpdateHandler(self.app_data_folder)

        # process the existing database once before we start the file observer
        class Event:
            src_path = os.path.join(cloud_folders.keys, KEY_MANAGEMENT_FILE)
        e = Event
        self.handler.dispatch(e)

        self.observer.schedule(self.handler, cloud_folders.keys)
        self.observer.start()
        if not pref.get_crypto_key():
            self.request_key()

    def request_exit(self):
        self.observer.stop()
        self.observer.join(latus.const.TIME_OUT)
        return self.observer.is_alive()

    def get_requesters(self):
        # delete really old (> 1 day) requests
        session = session_maker(self.app_data_folder)
        s = session()
        q = s.query(KeyRequestTable).all()
        if q:
            for row in q:
                if row.datetime < datetime.datetime.utcnow() - datetime.timedelta(days=1):
                    s.delete(row)
        s.commit()
        requesters = []
        rows = s.query(KeyRequestTable).all()
        for row in rows:
            requesters.append(row.requester)
        s.close()
        return requesters

    def get_requester_info(self, requester):
        pref = latus.preferences.Preferences(self.app_data_folder)
        cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
        requester_node_db = latus.nodedb.NodeDB(cloud_folders.nodedb, requester)
        return requester_node_db.get_user(), requester_node_db.get_computer()

    def request_key(self, timestamp=datetime.datetime.utcnow()):
        session = session_maker(self.app_data_folder)
        s = session()
        pref = latus.preferences.Preferences(self.app_data_folder)
        this_node_id = pref.get_node_id()
        request_table = KeyRequestTable(requester=this_node_id, datetime=timestamp)
        q = s.query(KeyRequestTable).filter_by(requester=this_node_id).first()
        if q:
            s.delete(q)
        s.add(request_table)
        s.commit()
        s.close()


def create_pref_and_node_db(app_data_folder):
    pref = latus.preferences.Preferences(app_data_folder)
    cloud_folders = latus.folders.CloudFolders(pref.get_cloud_root())
    node_db = latus.nodedb.NodeDB(cloud_folders.nodedb, pref.get_node_id(), pref.get_public_key(), True)
    return pref, node_db

if __name__ == '__main__':
    # just for debugging ...
    # this uses the files set up by test_key_manangement.py, so you have to run that first
    root = os.path.join('test_latus', 'data', 'key_management')
    latus.logger.init(os.path.join(root, 'log'))
    latus.logger.set_console_log_level(logging.INFO)
    app_data_folder = os.path.join(root, 'b', 'appdata')  # we are the responding node (node 'b')
    assert(os.path.exists(app_data_folder))
    km = KeyManagement(app_data_folder, True)
    km.start()