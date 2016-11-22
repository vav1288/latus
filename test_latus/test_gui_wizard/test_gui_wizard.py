
import os
import subprocess

import test_latus.tstutil


def test_gui_wizard_with_automa():

    print('DEBUG DEBUG DEBUG - STUB STUB STUB')
    return  # DEBUG

    # run automa with the automa script

    automa_script = os.path.abspath(os.path.join(test_latus.util.root_test_gui_wizard(), 'gui_wizard_automa.py'))
    pp = 'PYTHONPATH'
    save_python_path_env_var = os.getenv(pp)
    os.putenv(pp, os.path.join('c:', os.sep, 'Automa', 'library.zip'))
    python_27_exe = os.path.join('c:', os.sep, 'python27_32b', 'python.exe')
    check_call_parameters = [python_27_exe, automa_script]
    print('check_call parameters : %s' % str(check_call_parameters))
    subprocess.check_call(check_call_parameters)
    os.putenv(pp, save_python_path_env_var)

