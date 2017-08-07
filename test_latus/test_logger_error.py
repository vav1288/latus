
import latus.logger

# there seems to be a problem running Sentry in py.test - the errors never get logged


def test_logger_error(session_setup, module_setup):
    latus.logger.init()
    if False:
        # todo: right now, this flags an actual 'failed' in py.test - figure out how to have it not do that
        a = 1/0


def main():
    test_logger_error()

if __name__ == '__main__':
    main()
