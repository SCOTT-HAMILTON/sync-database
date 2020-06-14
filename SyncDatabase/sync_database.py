import click
from json import load
from os import makedirs, environ
from os.path import splitext, isfile, isdir, join
from SyncDatabase.sync_lib import *
import tempfile

@click.command()
@click.option('-d', '--debug', is_flag=True)
def cli(debug=True):

    config_file = environ['HOME']+'/.config/sync-database.conf'

    assert isfile(config_file)

    config = load(open(config_file, 'r'))

    hosts_config = config['hosts']

    hosts = hosts_config.keys()

    joinableClient,hosts_database_files,hosts_config,hosts = \
        connectClientToJoinableHosts(hosts,
                                    hosts_config,
                                    debug)
    if debug:
        print('Joinable hosts : ',hosts_config)
    else:
        print('Joinable hosts : ',hosts)

    run_hosts_setup_commands(joinableClient)

    with tempfile.TemporaryDirectory() as tmp:
        # Copying password tared files from remote hosts
        fetch_generated_hosts_tarballs(joinableClient,
                                        hosts_config,
                                        tmp,
                                        debug)

        # Cleaning hosts
        clean_hosts(joinableClient)

        # Creating a directory per database
        database_dirs = get_unique_database_dirs(hosts_database_files)
        if debug:
            print('database directory list : ',database_dirs)

        # Creating database dirs
        for directory in map(lambda db_file: tmp+'/'+db_file, database_dirs):
            makedirs(directory)

        # Moving fetched databases to their correspond temporary directories
        database_dirs_files_counter = dict([(db_file,0) for db_file in database_dirs])
        copy_fetched_databases_to_corresponding_tmp_dirs(
                database_dirs,
                hosts_config,
                database_dirs_files_counter,
                tmp,
                debug)

        # Copying local databases to their corresponding temporary directories
        copy_local_databases_to_corresponding_tmp_dirs(
                database_dirs_files_counter,
                tmp,
                debug)

        # Merging databases
        successfully_merged_databases = merge_databases(
                database_dirs_files_counter,
                tmp,
                debug)

        # Copying back the databases to the hosts
        copy_back_merged_databases_to_hosts(successfully_merged_databases,
                                            hosts_config,
                                            joinableClient,
                                            tmp,
                                            debug)

        # Copying the merged databases to local
        copy_merged_databases_to_local(successfully_merged_databases)

        # Create Backup tarball of the fetched databases
        from datetime import datetime
        backup_tarball_file = 'backup_'+str(datetime.now())+'.tar.xz'
        if debug:
            print('backup_tarball_file : '+backup_tarball_file)
        create_fetched_databases_backup_tarball(backup_tarball_file,
                                                database_dirs_files_counter,
                                                tmp)

        # Copy backup tarball to hosts
        copy_backup_tarball_to_hosts(backup_tarball_file,
                                    hosts_config,
                                    joinableClient,
                                    tmp,
                                    debug)

        # Copy backup tarball to local
        copy_backup_tarball_to_local(backup_tarball_file,tmp)
