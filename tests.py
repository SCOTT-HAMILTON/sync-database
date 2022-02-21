## Those tests require an internet connection
## if you want to sync with server,
## otherwise they need a adb connected android phone
## if you wan't to sync with you phone.
## Or both.
from SyncDatabase.sync_lib import DatabaseSyncher
from json import load
from os import environ
from os.path import isfile

config_file = environ["HOME"] + "/.config/sync-database.conf"
assert isfile(config_file)
config = load(open(config_file, "r"))
print("config : ", config)
hosts_config = config["hosts"]
databaseSyncher = DatabaseSyncher(
    hosts_config,
    config["passwords_directory"],
    config["phone_passwords_directory"],
    config["backup_history_directory"],
    config["phone_backup_history_directory"],
    config["adb_push_command"],
    config["adb_pull_command"],
    debug=True,
)
databaseSyncher.sync()
