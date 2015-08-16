
# This is run using automa (NOT regular Python).
# See http://www.getautoma.com/docs/python_integration .

import os
import time

from automa.api import *


def debug_print_all(message):
    print(message)
    print(find_all(Button()))
    print(find_all(CheckBox()))
    print(find_all(ComboBox()))
    print(find_all(ListItem()))
    print(find_all(MenuItem()))
    print(find_all(RadioButton()))
    print(find_all(Text()))
    print(find_all(TextField()))
    print(find_all(TreeItem()))
    print(find_all(Window()))
    # print(find_all(Image(os.path.join('test_latus', 'test_gui_wizard', 'next.png'))))

root = os.path.join('test_latus', 'test_gui_wizard')

# run the wizard

pp = 'PYTHONPATH'
python_path_env_var = os.path.abspath('.')
print('python_path_env_var', python_path_env_var)
save_python_path_env_var = os.getenv(pp)
os.putenv(pp, python_path_env_var)

python_exe = os.path.join('c:', os.sep, 'python34', 'python.exe')
test_program = os.path.abspath(os.path.join(root, 'gui_wizard_test.py'))

print('python_exe', python_exe)
print('test_program', test_program)

start(python_exe, test_program)

time.sleep(5)

# debug_print_all('start')

for node in range(0,2):
    switch_to('Latus Setup')

    # automa stopped being able to find the buttons, so now I have to use keyboard input :(

    # intro
    click('Latus Setup')

    press(ENTER)
    #click('Next Enter')  # not sure why it's Next Enter vs. Next, but that's what find_all(Button()) told me

    # cloud folder
    #click(find_all(ListItem())[0])  # top item
    press(TAB)
    press(TAB)
    press(SPACE)
    press(ENTER)
    #click('Next Enter')

    # latus folder
    press(ENTER)
    #click('Next Enter')

    # key
    press(ENTER)
    #click('Next Enter')

    # final
    press(ENTER)
    #click('Finish Enter')

    time.sleep(15)  # is there any way to test if the app is done instead of this sleep?

print('restoring', pp)
os.putenv(pp, save_python_path_env_var)
print('exiting', __name__)
