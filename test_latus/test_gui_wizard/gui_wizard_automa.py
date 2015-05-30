
# This is run using automa (NOT regular Python).
# See http://www.getautoma.com/docs/python_integration .

import os
import time

from automa.api import *

root = os.path.join('test_latus', 'test_gui_wizard')

# run the wizard

pp = 'PYTHONPATH'
python_path_env_var = os.path.abspath('.')
print('python_path_env_var', python_path_env_var)
save_python_path_env_var = os.getenv(pp)
os.putenv(pp, python_path_env_var)
python_exe = os.path.join('c:', os.sep, 'python34', 'python.exe')
test_program = os.path.abspath(os.path.join(root, 'gui_wizard.py'))

print('python_exe', python_exe)
print('test_program', test_program)

start(python_exe, test_program)

time.sleep(5)

# if you have a hard time finding the elements at this point, find_all() is handy, e.g.:
# print(find_all(Window()))
# print(find_all(Button()))

for node in range(0,2):
    switch_to('Latus Setup')

    # intro
    click('Next Enter')  # not sure why it's Next Enter vs. Next, but that's what find_all(Button()) told me

    # cloud folder
    click(find_all(ListItem())[0])  # top item
    click('Next Enter')

    # latus folder
    click('Next Enter')

    # key
    click('Next Enter')

    # final
    click('Finish Enter')

    time.sleep(15)  # is there any way to test if the app is done instead of this sleep?

os.putenv(pp, save_python_path_env_var)

