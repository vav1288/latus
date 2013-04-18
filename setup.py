
from cx_Freeze import setup, Executable

# see: http://cx_freeze.readthedocs.org/en/latest/index.html

#setup(
#    name='latus',
#    executables=['analyze.py', 'merge.py', 'propmtime.py'],
#    version='0.0',
#    packages=['.', 'latus', 'latus.test'],
#   author='James Abel',
#    author_email='j@abel.co',
#    url='www.lat.us',
#    license='LICENSE',
#    description='collection of file management utilities',
#    )

setup(
    name = "latus",
    version = "0.0",
    description = "collection of file management utilities",
    executables = [Executable("analyze.py")])