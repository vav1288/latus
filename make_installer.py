
import osnap.installer

APPLICATION_NAME = 'latus'
AUTHOR = 'abel'


def make_installer(verbose):
    osnap.installer.make_installer(AUTHOR, APPLICATION_NAME,
                                     'secure and unlimited storage across all your computers',
                                     'http://lat.us',
                                     ['latus'],
                                     verbose=verbose)


if __name__ == '__main__':
    make_installer(True)