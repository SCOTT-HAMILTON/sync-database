from SyncDatabase.sync_lib import DatabaseSyncher
from os import environ
from json import load
from os.path import isfile
import click

@click.command()
@click.option('-d', '--debug', is_flag=True)
def cli(debug=True):
    config_file = environ['HOME']+'/.config/sync-database.conf'
    assert isfile(config_file)
    config = load(open(config_file, 'r'))
    if debug:
        print("config : ",config)
    hosts_config = config['hosts']
    databaseSyncher = DatabaseSyncher(hosts_config,
                                      config['passwords_directory'],
                                      config['phone_passwords_directory'],
                                      config['backup_history_directory'],
                                      config['phone_backup_history_directory'],
                                      config['adb_push_command'],
                                      config['adb_pull_command'],
                                      debug)
    databaseSyncher.sync()

