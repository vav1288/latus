
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
    executables = [Executable("finddup.py"),
                   Executable("merge.py"),
                   Executable("propmtime.py"),
                   Executable("fsinfo.py"),
                   Executable("hash.py")]
)