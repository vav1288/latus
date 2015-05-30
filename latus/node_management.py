
import latus.preferences
import latus.nodedb
import latus.util
import latus.folders

def create(app_data_folder, cloud_folder, latus_folder):
    node_id = latus.util.new_node_id()
    pref = latus.preferences.Preferences(app_data_folder)
    pref.set_cloud_root(cloud_folder)
    pref.set_latus_folder(latus_folder)
    pref.set_node_id(node_id)
    pref.set_new_keys()
    # make the node db
    cloud_folders = latus.folders.CloudFolders(cloud_folder)
    node_db = latus.nodedb.NodeDB(cloud_folders.nodes, node_id, pref.get_public_key(), True)