from collections import OrderedDict
from functools import reduce
from gevent import joinall
from os import environ, listdir, makedirs, remove, rename
from os.path import basename, isfile, isdir, join, splitext
from pssh.clients.native import ParallelSSHClient
from shutil import copyfile
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

def connectClientToJoinableHosts(hosts, hosts_config):
    client = ParallelSSHClient(hosts,
            host_config=hosts_config,
            num_retries=1,
            timeout=3)
    print("Connected")
    print("Launching command...")
    outputs = client.run_command('ls ~/.local/share/passwords | egrep "*.kdbx"',
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
        if debug:
            print(new_hosts_config)
        if debug:
            print(hosts)
        joinableClient = ParallelSSHClient(hosts,
                host_config=new_hosts_config,
                num_retries=1,
                timeout=3)
    else:
        joinableClient = client
    return (joinableClient, hosts_databases_files, hosts_config, hosts)

def run_hosts_setup_commands(client):
    run_command(client, '[ -d  ~/passwords ] && rm -rf ~/passwords', consume_output=True)
    run_command(client, '[ -f ~/passwords ] && rm -f ~/passwords', consume_output=True)
    run_command(client, 'mkdir ~/passwords', consume_output=True)
    run_command(client, 'cp ~/.local/share/passwords/*.kdbx ~/passwords', consume_output=True)
    run_command(client, 'cd ~/passwords && tar  cvf ~/passwords.tar.gz *', consume_output=True)
    run_command(client, 'rm -rf ~/passwords', consume_output=True)

def fetch_generated_hosts_tarballs(client, hosts_config, temporary_dir, debug=False):
    copy_args = []
    for host,host_datas in hosts_config.items():
        host_dir = temporary_dir+'/'+host
        makedirs(host_dir)
        copy_args.append({
            'remote_file': '/home/'+host_datas['user']+'/passwords.tar.gz',
            'local_file':  host_dir+'/passwords.tar.gz',
        })
    if debug:
        print('copy_args : ',copy_args)
    joinall(client.copy_remote_file(
        '%(remote_file)s', '%(local_file)s', recurse=True,
        copy_args=copy_args), raise_error=True)

def clean_hosts(client):
    run_command(client, 'rm -rf ~/passwords.tar.gz', consume_output=True)

def get_unique_database_dirs(hosts_database_files):
    reduce_list_of_list = lambda l: reduce(lambda l1,l2: list(l1)+list(l2), l )
    unclean_databases_list = [ output.stdout for host,output in hosts_database_files.items() ]

    # Cleaning the database and removing duplicates to finally get a list of relative directories
    database_dirs = list(OrderedDict.fromkeys(
        reduce_list_of_list(unclean_databases_list)))
    database_dirs = list(map(lambda db_file: splitext(db_file)[0], database_dirs))
    return database_dirs

def copy_fetched_databases_to_corresponding_tmp_dirs(database_dirs,
                                                hosts_config,
                                                database_dirs_files_counter,
                                                temporary_dir,
                                                debug):
    for host,host_datas in hosts_config.items():
        host_dir = temporary_dir+'/'+host
        open_tarfile(host_dir+'/passwords.tar.gz').extractall(host_dir)
        remove(host_dir+'/passwords.tar.gz')
        db_files = [ f for f in listdir(host_dir) if isfile(join(host_dir,f)) ]
        if debug:
            print(host+' : ',db_files)
        for db_file in db_files:
            db_file_no_ext = splitext(db_file)[0]
            counter = database_dirs_files_counter[db_file_no_ext]
            database_dirs_files_counter[db_file_no_ext] += 1
            rename(host_dir+'/'+db_file,
                           temporary_dir+'/'+db_file_no_ext+'/db_'+str(counter))


def copy_local_databases_to_corresponding_tmp_dirs(database_dirs_files_counter,
                                                    temporary_dir,
                                                    debug=False):
    local_passwords_dir = environ['HOME']+'/.local/share/passwords'
    local_files = [ f for f in listdir(local_passwords_dir)
                        if splitext(f)[1] == '.kdbx'
                          and isfile(join(local_passwords_dir,f))
                  ]
    if debug:
        print("local databases : ",local_files)
    for db_file in local_files:
        db_file_no_ext = splitext(db_file)[0]
        counter = database_dirs_files_counter[db_file_no_ext]
        copyfile(local_passwords_dir+'/'+db_file,
                temporary_dir+'/'+db_file_no_ext+'/db_'+str(counter))
        database_dirs_files_counter[db_file_no_ext] += 1

def merge_databases(database_dirs_files_counter,
                    tmp,
                    debug=False):
    from MergeKeepass.keepassmerge import merge_databases
    import getpass
    successfully_merged_databases = []
    for db_dir,db_counter in database_dirs_files_counter.items():
        master_password = getpass.getpass()
        db_files = [ tmp+'/'+db_dir+'/db_'+str(count) for count in range(db_counter)]
        output_db = tmp+'/'+db_dir+'/'+db_dir+'.kdbx'
        if not merge_databases(db_files, output_db, master_password,
                continue_on_error=True):
            if debug:
                print("Successfully merged",len(db_files),db_dir,'files')
            successfully_merged_databases.append(output_db)
        else:
            print("Not successfully merged ",db_dir,'files')
    return successfully_merged_databases

def copy_back_merged_databases_to_hosts(successfully_merged_databases,
                                        hosts_config,
                                        client,
                                        temporary_dir,
                                        debug=False):
    copy_args = []
    local_files_to_copy = ' '.join(successfully_merged_databases)
    print('Merged databases to send to hosts : '+local_files_to_copy)
    for host,host_datas in hosts_config.items():
        remote_files = ' '.join(map(
            lambda db: '/home/'+host_datas['user']+'/.local/share/passwords/'+basename(db),
            successfully_merged_databases))
        copy_args.append({
            'local_file':  local_files_to_copy,
            'remote_file': remote_files,
        })
    if debug:
        print('copy_args : ',copy_args)
    joinall(client.copy_file(
        '%(local_file)s',
        '%(remote_file)s', recurse=True,
        copy_args=copy_args), raise_error=True)

def copy_merged_databases_to_local(successfully_merged_databases):
    for db_file in successfully_merged_databases:
        copyfile(db_file, environ['HOME']+'/.local/share/passwords/'+basename(db_file))

def create_fetched_databases_backup_tarball(backup_tarball_file,
                                            database_dirs_files_counter,
                                            temporary_dir):
    with open_tarfile(temporary_dir+'/'+backup_tarball_file, 'w:xz') as backup_tarball:
        for db_dir in database_dirs_files_counter.keys():
            backup_tarball.add(temporary_dir+'/'+db_dir)

def copy_backup_tarball_to_hosts(backup_tarball_file,
                                hosts_config,
                                client,
                                temporary_dir,
                                debug=False):
    run_command(client,
            '[ ! -d ~/.local/share/passwords/history_backup ] \
                    && mkdir ~/.local/share/passwords/history_backup',
                consume_output=True)
    copy_args = []
    for host,host_datas in hosts_config.items():
        copy_args.append({
            'local_file': temporary_dir+'/'+backup_tarball_file,
            'remote_file': '/home/'+host_datas['user']+'/.local/share/passwords/history_backup/'+backup_tarball_file,
        })
    joinall(client.copy_file(
        '%(local_file)s',
        '%(remote_file)s', recurse=True,
        copy_args=copy_args), raise_error=True)

def copy_backup_tarball_to_local(backup_tarball_file, temporary_dir):
    local_backup_history_dir = environ['HOME']+'/.local/share/passwords/history_backup'
    if not isdir(local_backup_history_dir):
        os.makedirs(local_backup_history_dir)
    copyfile(temporary_dir+'/'+backup_tarball_file, local_backup_history_dir+'/'+backup_tarball_file)

