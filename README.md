
## latus ##

# Introduction #

latus is a personal cloud client written in Python.

latus is provides synchronization of personal files across your computers.  It is similar in nature
to popular offerings such as DropBox, Google Drive and Microsoft One Drive except that latus is Open Source and
provides "zero knowledge" encryption.   latus is written in Python and uses commodity cloud storage - 
specifically Amazon Web Services (AWS) - to store (encrypted) files to the cloud and for the file system 
database.

# Why latus? #

I wanted to use cloud storage for my personal files, but I didn't like the idea of using
proprietary closed source solutions.  I wanted something that I could view and modify, and was written 
in a language I and others could readily understand.  So I wrote latus in Python and made it Open Source.

# How does latus work? #

Latus runs in the background as a client on your computers, usually as a desktop 'task bar' application.
It monitors the 'latus' directory and any file updates are (optionally) encrypted and sent to the cloud.
Currently AWS is used for the cloud storage itself.  File system changes are stored in AWS DynamoDB, 
an economical (even free for low usage) database.  AWS S3 is used as a file store of the (optionally) 
encrypted files.  Locally, each computer (known as a 'node') maintains a SQLite database that is 
essentially a cache of the cloud database.

When file system changes occur, the contents of the 'latus' directory are automatically synchronized across 
all of the latus nodes.

# Requirements #

As mentioned, latus uses AWS, so an AWS account is required.  latus uses AWS offerings that, as long 
as you stay below a usage threshold, are free.  Even though AWS free offerings may provide enough for personal use,
please be sure to check the AWS thresholds (e.g. for S3, DynamoDB, SNS, and SQS) so you don't end up with 
billing surprises.

# Benefits #

- Uses economical cloud storage (potentially free if you stay within the free tiers)
- 'zero knowledge' encryption of your personal files before they go to the cloud
- Open Source (Python)
  - Can view how your files are being handled
  - 'white label' cloud storage
- Enables fine-grained management of the use of cloud storage (future feature)

# Links #
Main web site:
www.lat.us


(trademarks are the property of their respective owners)
(latus is a registered trademark of James Abel)
