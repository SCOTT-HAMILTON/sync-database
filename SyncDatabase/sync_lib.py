from collections import OrderedDict
from functools import reduce
from gevent import joinall
from os import environ, listdir, makedirs, remove, rename
from os.path import basename, isfile, isdir, join, splitext
from pssh.clients.native import ParallelSSHClient
from shutil import copyfile
from subprocess import Popen, PIPE
from tarfile import open as open_tarfile

def print_outputs(outputs):
    print(outputs)
    for host,host_output in outputs.items():
        for line in host_output.stdout:
            print('['+host+']'+' <stdout> : '+line)

def get_outputs(outputs):
    print(outputs)
    stdouts = []
    for host,host_output in outputs.items():
        out = ''
        for line in host_output.stdout:
           out += line
        stdouts.append(out)
    return stdouts

def run_command(client, command, consume_output=False, **kwargs):
    output = client.run_command(command, kwargs, stop_on_errors=False,
            timeout=5)
    if consume_output:
        client.join(output, consume_output=True)
    else:
        client.join(output)
    for  host,host_output in output.items():
        if host_output.stderr == None:
            continue
        for line in host_output.stderr:
            print('['+host+']'+' <stderr> : '+line)
    return output


class DatabaseSyncher:

    def __init__(self,
            passwords_directory,
            phone_passwords_directory,
            backup_history_directory,
            phone_backup_history_directory,
            adb_push_command,
            adb_pull_command,
            debug):
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
        popen = Popen(command, stdout=PIPE, stderr=PIPE)
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

    def connectClientToJoinableHosts(self,
                                    hosts,
                                    hosts_config):
        client = ParallelSSHClient(hosts,
                host_config=hosts_config,
                num_retries=1,
                timeout=3)
        print("Connected")
        print("Launching command...")
        outputs = client.run_command('ls '+self.passwords_directory+' | egrep "*.kdbx"',
                stop_on_errors=False,
                timeout=3)
        hosts_databases_files = dict([(host,host_output) for host,host_output in outputs.items() ])

        # Filtering unjoinable hosts
        hosts_databases_files = \
                dict(filter(lambda host: host[1].exception == None, hosts_databases_files.items()))
        new_hosts_config = \
                dict(filter(lambda host: host[0] in hosts_databases_files.keys(), hosts_config.items()))
        joinableClient = None

        if len(new_hosts_config) < len(hosts_config):
            print("Reconnected client without unjoinable hosts")
            hosts = new_hosts_config.keys()
            hosts_config = new_hosts_config
            if self.debug:
                print(new_hosts_config)
            if self.debug:
                print(hosts)
            joinableClient = ParallelSSHClient(hosts,
                    host_config=new_hosts_config,
                    num_retries=1,
                    timeout=3)
        else:
            joinableClient = client
        return (joinableClient, hosts_databases_files, hosts_config, hosts)

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

    def clean_hosts(self, client):
        run_command(client, 'rm -rf ~/passwords.tar.gz', consume_output=True)

    def get_unique_database_dirs(self, hosts_database_files):
        reduce_list_of_list = lambda l: reduce(lambda l1,l2: list(l1)+list(l2), l )
        unclean_databases_list = [ output.stdout for host,output in hosts_database_files.items() ]

        # Cleaning the database and removing duplicates to finally get a list of relative directories
        database_dirs = list(OrderedDict.fromkeys(
            reduce_list_of_list(unclean_databases_list)))
        database_dirs = list(map(lambda db_file: splitext(db_file)[0], database_dirs))
        return database_dirs

    def copy_fetched_databases_to_corresponding_tmp_dirs(self,
                                                    database_dirs,
                                                    hosts_config,
                                                    database_dirs_files_counter):
        for host,host_datas in hosts_config.items():
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
        from MergeKeepass.keepassmerge import merge_databases
        import getpass
        successfully_merged_databases = []
        for db_dir,db_counter in database_dirs_files_counter.items():
            master_password = getpass.getpass()
            db_files = [ self.temporary_dir+'/'+db_dir+'/db_'+str(count) for count in range(db_counter)]
            output_db = self.temporary_dir+'/'+db_dir+'/'+db_dir+'.kdbx'
            if not merge_databases(db_files, output_db, master_password,
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
        copy_args = []
        local_files_to_copy = ' '.join(successfully_merged_databases)
        print('Merged databases to send to hosts : '+local_files_to_copy)
        for host,host_datas in hosts_config.items():
            remote_files = ' '.join(map(
                lambda db: '/home/'+host_datas['user']+'/'+self.relative_passwords_directory+'/'+basename(db),
                successfully_merged_databases))
            copy_args.append({
                'local_file':  local_files_to_copy,
                'remote_file': remote_files,
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
            os.makedirs(local_backup_history_dir)
        copyfile(self.temporary_dir+'/'+backup_tarball_file, local_backup_history_dir+'/'+backup_tarball_file)

    def copy_backup_tarball_to_phone(self,
                                    backup_tarball_file):
        self.run_phone_command(
                self.adb_push_command,
                source = self.temporary_dir+'/'+backup_tarball_file,
                dest = self.phone_backup_history_directory)
