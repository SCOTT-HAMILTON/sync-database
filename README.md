# sync-database

![Travis CI build status](https://travis-ci.org/SCOTT-HAMILTON/sync-database.svg?branch=master)

Keepass databases 1.x/2.x management utility to synchronize them
accross ssh servers and phones

# Building

This project is configured for setuptools

# How does it work

The script can be dissected in three parts :
 1. Fetching the database files
 2. Merging them together
 3. Sending them back, (and sending a backup archive of the fetched databases)

 - The first step fetches required databases from ssh servers, localhost and
 soon phone. Each configured server suitable for ssh should have its
keepass databases in `~/.local/share/passwords`. The way the script
knows which databases to merge together is by their name, databases
files of the same name accross ssh servers, localhost and phone will be merged
together. To illustrate that, let's imagine that you
have 2 ssh servers, A, B and C :

```
		user@A :
		~/.local/share/passwords/DB1.kdbx
		~/.local/share/passwords/MyDB.kdbx

		user@B :
		~/.local/share/passwords/DB1.kdbx
		~/.local/share/passwords/FamilyDB.kdbx

		user@C :
		~/.local/share/passwords/MyDB.kdbx
		~/.local/share/passwords/FamilyDB.kdbx
```

In this case the merging step described below will :

```
merge		user@A:~/.local/share/passwords/DB1.kdbx
				+
		user@B:~/.local/share/passwords/DB1.kdbx



merge		user@A:~/.local/share/passwords/MyDB.kdbx
				+
		user@C:~/.local/share/passwords/MyDB.kdbx


and merge	user@B:~/.local/share/passwords/FamilyDB.kdbx
				+
		user@C:~/.local/share/passwords/FamilyDB.kdbx
```

 - The merging step uses [merge-keepass](https://github.com/SCOTT-HAMILTON/merge-keepass)
 to merge the databases together. This updates/adds new groups, new entries and new fields.
 Unfortunatly, due to a bug in pykeepass, it cannot merge attachments. To merge,
 a password per database will be needed : in the case study above, you will be prompted for 3 passwords.
 The merging process can ignore errors and continue if not all databases are corrupted.
 But you should probably restore those corrupted database before synching because their modifications won't be merged.

 - The last step sends back the merged databases and an archive containing all the fetched
 databases to ssh servers, localhost and phone. Only the databases that merged successfully will be sent back.
 The archive tarball is named following this format : `"backup_YY-MM-DD %H:%M:%S.<microseconds>.tar.xz"`
 You have probably recognized the default python string format for datetime objects.
 This archive is copied to location `~/.local/share/passwords/history_backup` of all servers and localhost.

# Usage
```bash
$ sync_database
```

### Requirements
 - [parallel-ssh](https://github.com/ParallelSSH/parallel-ssh)
 - [merge-keepass](https://github.com/SCOTT-HAMILTON/merge-keepass)
 - python3

### Help

This is just a little project, but feel free to fork, change, extend or correct the code.

### TODO :
 - configuration
 - password configuration
 - phone adb integration

License
----
sync-database is delivered as it is under the well known MIT License

**References that helped**
 - [python3 documentation] : <https://docs.python.org/3>
 - [tarfile documentation] : <https://docs.python.org/3/library/tarfile.html>
 - [parallel-ssh documentation] : <http://parallel-ssh.readthedocs.io/en/latest>

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)



   [python3 documentation]: <https://docs.python.org/3>
   [tarfile documentation]: <https://docs.python.org/3/library/tarfile.html>
   [parallel-ssh documentation]: <http://parallel-ssh.readthedocs.io/en/latest>
