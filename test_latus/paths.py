
import os

def get_data_root():
    # todo: make this some sort of configuration
    return os.path.abspath(os.path.join('j:', os.sep, 'James', 'Projects', 'latus', 'test_latus', 'data'))

def root_test_gui_wizard():
    return os.path.join('test_latus', 'test_gui_wizard')