# Latus (lat.us)  #

## Introduction ##
[Latus](http://lat.us) is a core set of file indexing classes and a 
collection of file management utility applications built upon these
classes.

These applications provide efficient deduplication (AKA de-dupping), 
merging and syncing.  The core infrastructure consists of a set of 
classes that:

- Scan the file system and collect data, including calculating hashes.
- Write this data to a database (stored on the system the app is run on)
- Analyze folder contents (for things like duplicates)
- Compare the contents of two folders (for things like merging and sync-ing)

## scan ##

The `scan` application scans a file system folder and writes the metadata to
the database.  While scan doesn't do anything user-visible, it it very
handy to run by itself for testing purposes.  It gathers up the
required metadata as well as calculating hash values (if they
have not already been calculated).

## merge ##
`merge` determines what files need to be copied from one folder to
another to end up with a folder that contains a union of all the file
contents.  Note that since we compare contents (via hashes), only
the required files are copied over (essentially de-duping).

## sync ##
This sync is intended to synchronize two or more [nodes](node.html).
