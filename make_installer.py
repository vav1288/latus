
import os
import datetime

import osnap.installer

import latus


def make_installer():
    with open(os.path.join(latus.__application_name__, 'build.py'), 'w') as f:
        f.write('# programmatically generated - do not edit\n')
        f.write('\n')
        f.write('BUILD_TIMESTAMP = "%s"\n' % datetime.datetime.utcnow())

    osnap.installer.make_installer(latus.__python_version__, latus.__application_name__, latus.__version__,
                                   latus.__author__,
                                   'access all your files across all your computers - secure, free and open source',
                                   'www.lat.us')


if __name__ == '__main__':
    make_installer()
