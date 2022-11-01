from SyncDatabase.sync_lib import DatabaseSyncher
from os import environ
from json import load
from os.path import isfile
import click
from pprint import pprint

@click.command()
@click.option("-k", "--temp-dir", default=None)
@click.option("-m", "--master-password", default=None)
@click.option("-t", "--timeout", default=20)
@click.option("-d", "--debug", is_flag=True)
def cli(temp_dir, master_password, timeout, debug=True):
    config_file = environ["HOME"] + "/.config/sync-database.conf"
    assert isfile(config_file), f"config file {config_file} doesn't exist."
    config = load(open(config_file, "r"))
    if debug:
        print("config : ")
        pprint(config)
    hosts_config = config["hosts"]
    databaseSyncher = DatabaseSyncher(
        hosts_config,
        config["passwords_directory"],
        config["phone_passwords_directory"],
        config["backup_history_directory"],
        config["phone_backup_history_directory"],
        config["adb_push_command"],
        config["adb_pull_command"],
        master_password,
        temp_dir,
        timeout,
        debug,
    )
    databaseSyncher.sync()
