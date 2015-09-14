
# https://github.com/pyca/cryptography/issues/2039#issuecomment-125263375
# This is needed for freezing, until the above bug in cryptography is fixed.

import latus.logger


def patch_crypto_be_discovery():

    return  # this now fails for some reason

    """
    Monkey patches cryptography's backend detection.
    Objective: support pyinstaller freezing.
    """

    from cryptography.hazmat import backends

    try:
        from cryptography.hazmat.backends.commoncrypto.backend import backend as be_cc
    except ImportError:
        latus.logger.log.warning('ImportError')
        be_cc = None
    except RuntimeError:
        latus.logger.log.warning('RuntimeError')
        be_cc = None

    try:
        from cryptography.hazmat.backends.openssl.backend import backend as be_ossl
    except ImportError:
        be_ossl = None

    backends._available_backends_list = [
        be for be in (be_cc, be_ossl) if be is not None
    ]