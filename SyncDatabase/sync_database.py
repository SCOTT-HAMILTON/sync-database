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
    if debug:
        print("config : ",config)
    hosts_config = config['hosts']
    hosts = hosts_config.keys()
    databaseSyncher = DatabaseSyncher(
                                      config['passwords_directory'],
                                      config['phone_passwords_directory'],
                                      config['backup_history_directory'],
                                      config['phone_backup_history_directory'],
                                      config['adb_push_command'],
                                      config['adb_pull_command'],
                                      debug)

    joinableClient,hosts_database_files,hosts_config,hosts = \
        databaseSyncher.connectClientToJoinableHosts(hosts,
                                    hosts_config)
    if debug:
        print('Joinable hosts : ', hosts_config)
    else:
        print('Joinable hosts : ', hosts)
    databaseSyncher.run_hosts_setup_commands(joinableClient)

    with tempfile.TemporaryDirectory() as tmp:

        databaseSyncher.set_temporary_directory(tmp)

                    ###################################
                    #                                 #
                    #            FETCHING             #
                    #                                 #
                    ###################################

        # Copying password tared files from remote hosts
        databaseSyncher.fetch_generated_hosts_tarballs(joinableClient,
                                                        hosts_config)
        # Cleaning hosts
        databaseSyncher.clean_hosts(joinableClient)

        # Creating a directory per database
        database_dirs = databaseSyncher.get_unique_database_dirs(hosts_database_files)
        if debug:
            print('database directory list : ',database_dirs)

        # Creating database dirs
        for directory in map(lambda db_file: tmp+'/'+db_file, database_dirs):
            makedirs(directory)

        # Moving fetched databases to their correspond temporary directories
        database_dirs_files_counter = dict([(db_file,0) for db_file in database_dirs])
        databaseSyncher.copy_fetched_databases_to_corresponding_tmp_dirs(
                database_dirs,
                hosts_config,
                database_dirs_files_counter)

        # Copying local databases to their corresponding temporary directories
        databaseSyncher.copy_local_databases_to_corresponding_tmp_dirs(
                        database_dirs_files_counter)

        # Copying phone databases to their corresponding temporary directories
        databaseSyncher.copy_phone_databases_to_corresponding_tmp_dirs(
                        database_dirs_files_counter)

                    ###################################
                    #                                 #
                    #            MERGING              #
                    #                                 #
                    ###################################

        # Merging databases
        successfully_merged_databases = databaseSyncher.merge_databases(
                database_dirs_files_counter)
        if len(successfully_merged_databases) == 0:
            print("0 database successfully merged, exitting.")
            exit(1)

                    ###################################
                    #                                 #
                    #        SENDING BACK             #
                    #                                 #
                    ###################################

        # Copying back the databases to the hosts
        databaseSyncher.copy_back_merged_databases_to_hosts(successfully_merged_databases,
                                            hosts_config,
                                            joinableClient)

        # Copying the merged databases to local
        databaseSyncher.copy_merged_databases_to_local(successfully_merged_databases)

        # Copying the merged databases to phone
        databaseSyncher.copy_merged_databases_to_phone(successfully_merged_databases)

        # Create Backup tarball of the fetched databases
        from datetime import datetime
        # replaces some characters because of adb-sync bug
        backup_tarball_file = 'backup_'+str(datetime.now().isoformat().replace(':','_').replace('.', '-'))+'.tar.xz'
        if debug:
            print('backup_tarball_file : '+backup_tarball_file)
        databaseSyncher.create_fetched_databases_backup_tarball(
                                            backup_tarball_file,
                                            database_dirs_files_counter)

        # Copy backup tarball to hosts
        databaseSyncher.copy_backup_tarball_to_hosts(backup_tarball_file,
                                    hosts_config,
                                    joinableClient)

        # Copy backup tarball to local
        databaseSyncher.copy_backup_tarball_to_local(backup_tarball_file)

        # Copy backup tarball to phone
        databaseSyncher.copy_backup_tarball_to_phone(backup_tarball_file)
