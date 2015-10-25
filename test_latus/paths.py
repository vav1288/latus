
import os


def get_data_root():

    # todo: make this some sort of configuration
    #projects_root = os.path.join('j:', os.sep, 'James', 'Projects', )
    projects_root = os.path.join(os.sep, 'Users', 'james', 'Documents', 'james', 'projects')

    return os.path.abspath(os.path.join(projects_root, 'latus', 'test_latus', 'data'))


def root_test_gui_wizard():
    return os.path.join('test_latus', 'test_gui_wizard')