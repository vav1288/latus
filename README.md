
## latus ##

# Introduction #

latus is a personal cloud client written in Python.

latus is provides synchronization of your personal files across your computers.  It is similar in nature
to popular offerings such as DropBox, Google Drive and Microsoft One Drive.  latus is Open Source and 
written in Python.

# Why latus? #

Well, it's Open Source :).  While today's personal cloud storage are quite capable, 
They generally do not open source their clients.  Some people would prefer to run software they 
can view and customize, and latus offers this.

# How does latus work? #

Latus runs in the background as a client on your computers, usually as a desktop 'task bar' application.
It monitors the 'latus' directory and any updates are (optionally) encrypted and sent to the cloud.
Currently AWS is used for the 'cloud' storage itself.  File system changes are stored in AWS DynamoDB, 
a low cost (even free for low usage) database.  AWS S3 is used as a file store of the (optionally) 
encrypted files.  Locally, each computer (known as a 'node') maintains a SQLite database that is 
essentially a cache of the cloud database.

When file system changes occur, the contents of the 'latus' directory are synchronized across 
all of the latus nodes.

# Requirements #

As mentioned, latus uses AWS, so an AWS account is required.  latus uses AWS offerings that, as long 
as you stay below a usage threshold, are free.  AWS free offerings may provide enough for personal use,
but be sure to check with the AWS thresholds (e.g. S3, DynamoDB, SNS, SQS).

# Benefits #

- Uses free or low cost cloud storage
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
