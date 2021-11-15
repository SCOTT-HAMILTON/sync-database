from MergeKeepass.keepassmerge import KeepassMerger
from collections import OrderedDict
from gevent import joinall
from os import environ, listdir, makedirs, remove, rename
from os.path import basename, splitext, isfile, isdir, join
from pssh.clients.native import ParallelSSHClient
from pssh.config import HostConfig
from shutil import copyfile
from subprocess import Popen, PIPE
from tarfile import open as open_tarfile
import getpass
import tempfile

def run_command(client, command, consume_output=False, **kwargs):
    outputs = client.run_command(command, kwargs, stop_on_errors=False,
            read_timeout=10)
    if consume_output:
        client.join(outputs, consume_output=True)
    else:
        client.join(outputs)
    for host_output in outputs:
        if host_output.stderr == None:
            continue
        for line in host_output.stderr:
            print('['+host_output.host+']'+' <stderr> : '+line)
    return outputs

def clean_hosts(client):
    run_command(client, 'rm -rf ~/passwords.tar.gz', consume_output=True)

def get_unique_database_dirs(database_files):
    # Cleaning the database and removing duplicates to finally get a list of relative directories
    database_dirs = list(OrderedDict.fromkeys(
        database_files))
    database_dirs = list(map(lambda db_file: splitext(db_file)[0], database_dirs))
    return database_dirs

def dict_to_hosts_config(h_dict):
    result = []
    for host,config in h_dict.items():
        result.append(HostConfig(user=config["user"], port=config["port"]))
    return result

class DatabaseSyncher:
    """DatabaseSyncher Class"""
    def __init__(self,
            hosts_config,
            passwords_directory,
            phone_passwords_directory,
            backup_history_directory,
            phone_backup_history_directory,
            adb_push_command,
            adb_pull_command,
            debug=False):
        """For further details, checkout the README.md.

            :param hosts_config: dictionnary of host-configurations

            :param passwords_directory:
                directory where are located the Keepass database files
                in every host (~ is supported)

            :param phone_passwords_directory:
                same as passwords_directory but for your phone

            :param backup_history_directory:
                directory where the backup files will be stored on every host.
                (~ is supported)

            :param phone_backup_history_directory:
                same as backup_history_directory but for your phone

            :param adb_push_command: adb configuration for pushing files to the phone
            :param adb_pull_command: adb configuration for pulling files to the phone
            :param debug: enable debugging, default is False
        """
        self.merger = KeepassMerger()
        self.hosts = list(hosts_config.keys())
        self.hosts_config = hosts_config
        self.debug = debug
        self.passwords_directory = passwords_directory
        self.relative_passwords_directory = passwords_directory[2:]
        self.phone_passwords_directory = phone_passwords_directory
        self.backup_history_directory = backup_history_directory
        self.phone_backup_history_directory = phone_backup_history_directory
        self.relative_backup_history_directory = self.backup_history_directory[2:]
        self.adb_push_command = adb_push_command
        self.adb_pull_command = adb_pull_command
        if self.debug:
            print("passwords directory : "+self.passwords_directory)
            print("relative passwords directory : "+self.relative_passwords_directory)
            print("phone passwords directory : "+self.phone_passwords_directory)
            print("backup history directory : "+self.backup_history_directory)
            print("relative backup history directory : "+self.relative_backup_history_directory)
            print("phone backup history directory : "+self.phone_backup_history_directory)
            print("adb push command : ",self.adb_push_command)
            print("adb pull command : ",self.adb_pull_command)

    def run_phone_command(self, adb_command, source, dest):
        command = [ ]
        command.append(adb_command['command'])
        args_list = adb_command['args'].split(' ')

        for arg in args_list:
            if arg == '{source}':
                arg = arg.format(source=source)
            elif arg == '{dest}':
                arg = arg.format(dest=dest)
            command.append(arg)
        if self.debug:
            print("adb command : ",command)
        popen = Popen(command, stdout=PIPE, stderr=PIPE, shell=False)
        coms = popen.communicate()
        if self.debug:
            # Printing stdout
            if coms[0]:
                print(coms[0])
            # Printing stderr
            if coms[1]:
                print(coms[1])
        if popen.returncode == 0:
            print('Fetched phone databases')
        else:
            print("Couldn't fetch phone databases")

    def set_temporary_directory(self, temporary_directory):
        self.temporary_dir = temporary_directory

    def connectClientToJoinableHosts(self):
        client = ParallelSSHClient(self.hosts,
                host_config=dict_to_hosts_config(self.hosts_config),
                num_retries=1,
                timeout=10.0)
        print("Connected")
        print("Launching command...")
        outputs = client.run_command('ls '+self.passwords_directory+' | egrep "*.kdbx"',
                stop_on_errors=False,
                read_timeout=10)
        hosts_databases_files = dict([(host_output.host,host_output) for host_output in outputs ])

        # Filtering unjoinable hosts
        hosts_databases_files = \
                dict(filter(lambda host: host[1].exception == None, hosts_databases_files.items()))
        new_hosts_config = \
                dict(filter(lambda host: host[0] in hosts_databases_files.keys(), self.hosts_config.items()))
        new_hosts = list(new_hosts_config.keys())
        joinableClient = None

        if len(new_hosts_config) < len(self.hosts_config):
            print("Reconnected client without unjoinable hosts")
            if self.debug:
                print(new_hosts_config)
            if self.debug:
                print(new_hosts)
            joinableClient = ParallelSSHClient(new_hosts,
                    host_config=dict_to_hosts_config(new_hosts_config),
                    num_retries=1,
                    timeout=10.0)
        else:
            joinableClient = client
        return (joinableClient, hosts_databases_files, new_hosts_config, new_hosts)

    def run_hosts_setup_commands(self,
                                client):
        run_command(client, '[ -d  ~/passwords ] && rm -rf ~/passwords', consume_output=True)
        run_command(client, '[ -f ~/passwords ] && rm -f ~/passwords', consume_output=True)
        run_command(client, 'mkdir ~/passwords', consume_output=True)
        run_command(client, 'cp '+self.passwords_directory+'/*.kdbx ~/passwords', consume_output=True)
        run_command(client, 'cd ~/passwords && tar  cvf ~/passwords.tar.gz *', consume_output=True)
        run_command(client, 'rm -rf ~/passwords', consume_output=True)

    def fetch_generated_hosts_tarballs(self,
                                    client,
                                    hosts_config):
        copy_args = []
        for host,host_datas in hosts_config.items():
            host_dir = self.temporary_dir+'/'+host
            makedirs(host_dir)
            copy_args.append({
                'remote_file': '/home/'+host_datas['user']+'/passwords.tar.gz',
                'local_file':  host_dir+'/passwords.tar.gz',
            })
        if self.debug:
            print('copy_args : ',copy_args)
        joinall(client.copy_remote_file(
            '%(remote_file)s', '%(local_file)s', recurse=True,
            copy_args=copy_args), raise_error=True)

    def get_local_database_files(self):
        local_passwords_dir = environ['HOME']+'/'+self.relative_passwords_directory
        local_files = [ f for f in listdir(local_passwords_dir)
                            if splitext(f)[1] == '.kdbx'
                              and isfile(join(local_passwords_dir,f))
                      ]
        return local_files

    def copy_fetched_databases_to_corresponding_tmp_dirs(self,
                                                    database_dirs,
                                                    hosts_config,
                                                    database_dirs_files_counter):
        for host,_ in hosts_config.items():
            host_dir = self.temporary_dir+'/'+host
            open_tarfile(host_dir+'/passwords.tar.gz').extractall(host_dir)
            remove(host_dir+'/passwords.tar.gz')
            db_files = [ f for f in listdir(host_dir) if isfile(join(host_dir,f)) ]
            if self.debug:
                print(host+' : ',db_files)
            for db_file in db_files:
                db_file_no_ext = splitext(db_file)[0]
                counter = database_dirs_files_counter[db_file_no_ext]
                database_dirs_files_counter[db_file_no_ext] += 1
                rename(host_dir+'/'+db_file,
                               self.temporary_dir+'/'+db_file_no_ext+'/db_'+str(counter))


    def copy_local_databases_to_corresponding_tmp_dirs(self,
                                                    database_dirs_files_counter):
        local_passwords_dir = environ['HOME']+'/'+self.relative_passwords_directory
        local_files = [ f for f in listdir(local_passwords_dir)
                            if splitext(f)[1] == '.kdbx'
                              and isfile(join(local_passwords_dir,f))
                      ]
        if self.debug:
            print("local databases : ",local_files)
        for db_file in local_files:
            db_file_no_ext = splitext(db_file)[0]
            counter = database_dirs_files_counter[db_file_no_ext]
            copyfile(local_passwords_dir+'/'+db_file,
                    self.temporary_dir+'/'+db_file_no_ext+'/db_'+str(counter))
            database_dirs_files_counter[db_file_no_ext] += 1

    def copy_phone_databases_to_corresponding_tmp_dirs(self,
                                                    database_dirs_files_counter):
        phone_dir = self.temporary_dir+'/phone'
        makedirs(phone_dir)
        self.run_phone_command(
                    self.adb_pull_command,
                    source = self.phone_passwords_directory+'/*.kdbx',
                    dest = phone_dir)
        phone_files = [ f for f in listdir(phone_dir)
                            if splitext(f)[1] == '.kdbx'
                              and isfile(join(phone_dir,f))
                      ]
        if self.debug:
            print("phone databases : ", phone_files)
        for db_file in phone_files:
            db_file_no_ext = splitext(db_file)[0]
            counter = database_dirs_files_counter[db_file_no_ext]
            copyfile(phone_dir+'/'+db_file,
                    self.temporary_dir+'/'+db_file_no_ext+'/db_'+str(counter))
            database_dirs_files_counter[db_file_no_ext] += 1

    def merge_databases(self,
                        database_dirs_files_counter):
        successfully_merged_databases = []
        for db_dir,db_counter in database_dirs_files_counter.items():
            master_password = getpass.getpass(prompt=f'Password for {db_dir}: ')
            db_files = [ self.temporary_dir+'/'+db_dir+'/db_'+str(count) for count in range(db_counter)]
            output_db = self.temporary_dir+'/'+db_dir+'/'+db_dir+'.kdbx'
            if not self.merger.merge_databases(db_files, output_db, master_password,
                    continue_on_error=True):
                if self.debug:
                    print("Successfully merged",len(db_files),db_dir,'files')
                successfully_merged_databases.append(output_db)
            else:
                print("Not successfully merged ",db_dir,'files')
        return successfully_merged_databases

    def copy_back_merged_databases_to_hosts(self,
                                            successfully_merged_databases,
                                            hosts_config,
                                            client):
        print('Merged databases to send to hosts : ',successfully_merged_databases)
        for db_file in successfully_merged_databases:
            copy_args = []
            for host,host_datas in hosts_config.items():
                remote_file = '/home/'+host_datas['user']+'/'+self.relative_passwords_directory+'/'+basename(db_file)
                copy_args.append({
                    'local_file':  db_file,
                    'remote_file': remote_file,
                })
            if self.debug:
                print('copy_args : ',copy_args)
            joinall(client.copy_file(
                '%(local_file)s',
                '%(remote_file)s', recurse=True,
                copy_args=copy_args), raise_error=True)

    def copy_merged_databases_to_local(self,
                                    successfully_merged_databases):
        for db_file in successfully_merged_databases:
            copyfile(db_file, environ['HOME']+'/'+self.relative_passwords_directory+'/'+basename(db_file))

    def copy_merged_databases_to_phone(self,
                                    successfully_merged_databases):
        for db_file in successfully_merged_databases:
            self.run_phone_command(
                        self.adb_push_command,
                        source = db_file,
                        dest = self.phone_passwords_directory)


    def create_fetched_databases_backup_tarball(self,
                                                backup_tarball_file,
                                                database_dirs_files_counter):
        with open_tarfile(self.temporary_dir+'/'+backup_tarball_file, 'w:xz') as backup_tarball:
            for db_dir in database_dirs_files_counter.keys():
                backup_tarball.add(self.temporary_dir+'/'+db_dir)

    def copy_backup_tarball_to_hosts(self,
                                    backup_tarball_file,
                                    hosts_config,
                                    client):
        run_command(client,
                '[ ! -d '+self.backup_history_directory+' ] \
                        && mkdir '+self.backup_history_directory,
                    consume_output=True)
        copy_args = []
        for host,host_datas in hosts_config.items():
            copy_args.append({
                'local_file': self.temporary_dir+'/'+backup_tarball_file,
                'remote_file': '/home/'+host_datas['user']+'/.local/share/passwords/history_backup/'+backup_tarball_file,
            })
        joinall(client.copy_file(
            '%(local_file)s',
            '%(remote_file)s', recurse=True,
            copy_args=copy_args), raise_error=True)

    def copy_backup_tarball_to_local(self,
                                    backup_tarball_file):
        local_backup_history_dir = environ['HOME']+'/'+self.relative_backup_history_directory
        if not isdir(local_backup_history_dir):
            makedirs(local_backup_history_dir)
        copyfile(self.temporary_dir+'/'+backup_tarball_file, local_backup_history_dir+'/'+backup_tarball_file)

    def copy_backup_tarball_to_phone(self,
                                    backup_tarball_file):
        self.run_phone_command(
                self.adb_push_command,
                source = self.temporary_dir+'/'+backup_tarball_file,
                dest = self.phone_backup_history_directory)

    def sync(self):
        joinableClient,host_database_files_result,joinable_hosts_config,joinable_hosts = \
            self.connectClientToJoinableHosts()
        if self.debug:
            print('Joinable hosts : ', joinable_hosts_config)
        else:
            print('Joinable hosts : ', joinable_hosts)
        self.run_hosts_setup_commands(joinableClient)

        with tempfile.TemporaryDirectory() as tmp:
            self.set_temporary_directory(tmp)
                        ###################################
                        #            FETCHING             #
                        ###################################
            # Copying password tared files from remote hosts
            self.fetch_generated_hosts_tarballs(joinableClient,
                                                            joinable_hosts_config)
            # Cleaning hosts
            clean_hosts(joinableClient)
            host_database_files = []
            for output in host_database_files_result.values():
                for line in output.stdout:
                    host_database_files.append(line)
            if self.debug:
                print('host database file list : ',host_database_files)
            # Add local databases to hosts database files
            local_database_files = self.get_local_database_files()
            if self.debug:
                print('local database file list : ',local_database_files)
            database_files = host_database_files + local_database_files
            assert len(database_files) > 0
            # Creating a directory per database
            database_dirs = get_unique_database_dirs(database_files)
            if self.debug:
                print('database directory list : ',database_dirs)
            # Creating database dirs
            for directory in map(lambda db_file: tmp+'/'+db_file, database_dirs):
                makedirs(directory)
            # Moving fetched databases to their correspond temporary directories
            database_dirs_files_counter = dict([(db_file,0) for db_file in database_dirs])
            self.copy_fetched_databases_to_corresponding_tmp_dirs(
                    database_dirs,
                    joinable_hosts_config,
                    database_dirs_files_counter)
            # Copying local databases to their corresponding temporary directories
            self.copy_local_databases_to_corresponding_tmp_dirs(
                            database_dirs_files_counter)
            # Copying phone databases to their corresponding temporary directories
            self.copy_phone_databases_to_corresponding_tmp_dirs(
                            database_dirs_files_counter)
                        ###################################
                        #            MERGING              #
                        ###################################
            # Merging databases
            successfully_merged_databases = self.merge_databases(
                    database_dirs_files_counter)
            if len(successfully_merged_databases) == 0:
                print("0 database successfully merged, exitting.")
                return 1
                        ###################################
                        #        SENDING BACK             #
                        ###################################
            # Copying back the databases to the hosts
            self.copy_back_merged_databases_to_hosts(successfully_merged_databases,
                                                joinable_hosts_config,
                                                joinableClient)
            # Copying the merged databases to local
            self.copy_merged_databases_to_local(successfully_merged_databases)
            # Copying the merged databases to phone
            self.copy_merged_databases_to_phone(successfully_merged_databases)
            # Create Backup tarball of the fetched databases
            from datetime import datetime
            # replaces some characters because of adb-sync bug
            backup_tarball_file = 'backup_'+str(datetime.now().isoformat().replace(':','_').replace('.', '-'))+'.tar.xz'
            if self.debug:
                print('backup_tarball_file : '+backup_tarball_file)
            self.create_fetched_databases_backup_tarball(
                                                backup_tarball_file,
                                                database_dirs_files_counter)
            # Copy backup tarball to hosts
            self.copy_backup_tarball_to_hosts(backup_tarball_file,
                                        joinable_hosts_config,
                                        joinableClient)
            # Copy backup tarball to local
            self.copy_backup_tarball_to_local(backup_tarball_file)
            # Copy backup tarball to phone
            self.copy_backup_tarball_to_phone(backup_tarball_file)


def print_outputs(outputs):
    print(outputs)
    for host,host_output in outputs.items():
        for line in host_output.stdout:
            print('['+host+']'+' <stdout> : '+line)

def get_outputs(outputs):
    print(outputs)
    stdouts = []
    for _,host_output in outputs.items():
        out = ''
        for line in host_output.stdout:
           out += line
        stdouts.append(out)
    return stdouts

