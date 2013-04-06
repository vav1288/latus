from distutils.core import setup
import py2exe

setup(
    name='latus',
    console=['analyze.py', 'merge.py', 'propmtime.py'],
    version='0.0',
    packages=['.'],
    author='James Abel',
    author_email='j@abel.co',
    url='www.lat.us',
    license='LICENSE',
    description='collection of file management utilities',
    )
