
import osnap.installer

import latus


def make_installer():
    osnap.installer.make_installer(latus.__python_version__, latus.__application_name__, latus.__version__,
                                   latus.__author__,
                                   'access all your files across all your computers - secure, free and open source',
                                   'www.lat.us')


if __name__ == '__main__':
    make_installer()
