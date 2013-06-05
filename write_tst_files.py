
from latus.test import test_latus

# funny looking name to avoid matching nosetests pattern match (otherwise I would have had 'test' in the name)

# This just gets us the ability to write the test files so we can see them
# (since normally the test infrastructure cleans them up).
# Mainly used for manual testing.

if __name__ == "__main__":
    test = test_latus.test_latus()
    print ("writing test files to:", test_latus.get_root())
    print ("(does not run the actual tests)")
    test.write_files(force=True)

    test_latus.write_non_execution_test_dir_files()