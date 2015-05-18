
import os
import subprocess

def test_gui_wizard_with_automa():
    # run automa with the automa script

    automa_script = os.path.join('test_latus', 'gui_wizard_automa.py')
    pp = 'PYTHONPATH'
    save_python_path_env_var = os.getenv(pp)
    os.putenv(pp, os.path.join('c:', os.sep, 'Automa', 'library.zip'))
    python_27_exe = os.path.join('c:', os.sep, 'python27', 'python.exe')
    subprocess.check_call([python_27_exe, automa_script])
    os.putenv(pp, save_python_path_env_var)

