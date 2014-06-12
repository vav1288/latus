
from cx_Freeze import setup, Executable

setup(
    name = "latus",
    version = "0.0",
    author='James Abel',
    author_email='j@abel.co',
    url='www.lat.us',
    license='LICENSE',
    description = "collection of file management utilities",
    py_modules=['*'],
    executables = [Executable("scan.py"),
                   Executable("merge.py"),
                   Executable("sync.py")]
)