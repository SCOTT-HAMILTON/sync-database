<h1 align="center">sync-database</h1>

<p align="center">
      <a href="https://scott-hamilton.mit-license.org/"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-525252.svg?labelColor=292929&logo=creative%20commons&style=for-the-badge" /></a>
	  <a href="https://github.com/SCOTT-HAMILTON/sync-database/actions"><img alt="Build Status" src="https://img.shields.io/github/workflow/status/SCOTT-HAMILTON/sync-database/CI?logo=github-actions&style=for-the-badge" /></a>
	  <a href="https://www.codacy.com/gh/SCOTT-HAMILTON/sync-database/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=SCOTT-HAMILTON/sync-database&amp;utm_campaign=Badge_Grade"><img alt="Code Quality" src="https://img.shields.io/codacy/grade/e7251769529e4b04bbb4ea94568e1268?logo=codacy&style=for-the-badge" /></a>
</p>

Keepass databases 1.x/2.x management utility to synchronize them
accross ssh servers and phones

## Building

This project is configured for setuptools

## How does it work

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

## Usage
```shell_session
$ sync_database
```

## Configuration
Copy and edit this to `~/.config/sync-database.conf` :
```json
{
    "adb_pull_command": {
        "args": "-R {source} {dest}",
        "command": "adb-sync"
    },
    "adb_push_command": {
        "args": "{source} {dest}",
        "command": "adb-sync"
    },
    "hosts": {
        "213.119.171.157": {
            "port": 22,
            "user": "myuser"
        },
        "MY-LAPTOP": {
            "port": 22,
            "user": "mylaptopuser"
        }
    },
    "backup_history_directory": "~/.local/share/passwords/history_backup",
    "passwords_directory": "~/.local/share/passwords",
    "phone_backup_history_directory": "/storage/sdcard1/passwords/history_backup",
    "phone_passwords_directory": "/storage/sdcard1/passwords"
}
```
**adb_pull_command**.*args*: argument format string to pass to **adb_pull_command**.*command* command.
`{source}` and `{dest}` corresponds respectively to the remote file that will be pulled, and the destination file/folder where it will be stored locally.
I use `adb-sync`, but most of you would like to configure this with the `adb` binary from android-platform-tools like this :
```json
"adb_pull_command": {
	"args": "pull {source} {dest}",
	"command": "adb"
},
"adb_push_command": {
	"args": "push {source} {dest}",
	"command": "adb"
},
```
**hosts**.*\<destination\>*: IP or hostname of the host. The same as for the `ping` or `ssh` commands' argument.

**hosts**.**\<destination\>**.*port*: The ssh port that will be used when connecting to this host.

**hosts**.**\<destination\>**.*user*: The ssh user that will be used when connecting to this host.

**backup_history_directory**: Directory where the backup files will be stored. (~ is supported)

**passwords_directory**: Directory where are located the Keepass database files in every host (~ is supported)

**phone_backup_history_directory**: Same as **backup_history_directory** but on your phone. (doesn't support ~)

**phone_passwords_directory**: Same as **passwords_directory**. (doesn't support ~)

## Warning
The **backup_history_directory** directory is never cleaned up (it's a backup), and is filled up in every hosts (for redundancy) on every call to `sync_database`. Same goes to **phone_backup_history_directory**. Each backup file in this folder is a dated XZ compressed file that contains the Keepass databases of all the hosts+phone that could be fetched when `sync_database` was run. Normally, this shouldn't take a lot of space, mine uses about **3 Mio** of space with **2 hosts** and **a phone** after **51 calls** to `sync_database` (4 syncs per month for 1 year). But that obviously does depend on the size of your database files, on the the number of hosts you sync and on how frequently you sync your databases.

## Requirements
 - [parallel-ssh](https://github.com/ParallelSSH/parallel-ssh)
 - [merge-keepass](https://github.com/SCOTT-HAMILTON/merge-keepass)
 - click

## Help
This is just a little project, but feel free to fork, change, extend or correct the code.

## License
sync-database is delivered as it is under the well known MIT License

**References that helped**
 - [python3 documentation] : <https://docs.python.org/3>
 - [tarfile documentation] : <https://docs.python.org/3/library/tarfile.html>
 - [parallel-ssh documentation] : <http://parallel-ssh.readthedocs.io/en/latest>

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

   [python3 documentation]: <https://docs.python.org/3>
   [tarfile documentation]: <https://docs.python.org/3/library/tarfile.html>
   [parallel-ssh documentation]: <http://parallel-ssh.readthedocs.io/en/latest>
