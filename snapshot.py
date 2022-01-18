#apt-get install libpq-dev python-dev
#pip install boto3
#pip install psycopg2
import os
import boto3
import time
import psycopg2
import subprocess
from datetime import datetime, timezone
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


TODAY               = (datetime.today()).date()

PROJECT             = os.environ['PROJECT']
REGION              = os.environ['AWS_REGION']
SUBNET_DESTINO      = os.environ['SUBNET_DESTINO']
REGION_DESTINO      = os.environ['REGION_DESTINO']
RDS_CLIENT          = boto3.client('rds', REGION)
RDS_DESTINO         = boto3.client('rds', REGION_DESTINO)
INSTANCE_CLASS      = os.environ['INSTANCE_CLASS']

ID_CUENTA           = os.environ['ID_CUENTA']
DB_USER             = os.environ['DB_USER']
DB_PASSWORD         = os.environ['DB_PASSWORD']
DB_PORT             = os.environ['DB_PORT']
DB_DATABASE         = os.environ['DB_DATABASE']

DB_HOST_DESTINO     = os.environ['DB_HOST_DESTINO']
DB_USER_DESTINO     = os.environ['DB_USER_DESTINO']
DB_PASSWORD_DESTINO = os.environ['DB_PASSWORD_DESTINO']
DB_PORT_DESTINO     = os.environ['DB_PORT_DESTINO']
DB_DATABASE_DESTINO = os.environ['DB_DATABASE_DESTINO']


def upload_to_s3(file_full_path, dest_file):
    """
    Upload a file to an AWS S3 bucket.
    """
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_full_path, AWS_BUCKET_NAME, AWS_BUCKET_PATH + dest_file)
        os.remove(file_full_path)
    except boto3.exceptions.S3UploadFailedError as exc:
        print(exc)
        exit(1)


def download_from_s3(backup_s3_key, dest_file):
    """
    Download a file to an AWS S3 bucket.
    """
    s3_client = boto3.resource('s3')
    try:
        s3_client.meta.client.download_file(AWS_BUCKET_NAME, backup_s3_key, dest_file)
    except Exception as e:
        print(e)
        exit(1)

def get_info_snapshot_rds_today(is_arn):
    """
    Get name last snapshot from db rds. is_arn arn, id
    """
    snapshots = RDS_CLIENT.describe_db_snapshots(
        Filters=[
            {
                'Name': 'db-instance-id',
                'Values': [
                    os.environ['NAME_RDS'],
                ]
            },
        ]
    )

    for i in snapshots['DBSnapshots']:
        if i['SnapshotCreateTime'].date() == TODAY:
            if is_arn:
                snapshot_today = i['DBSnapshotArn']
            else:
                snapshot_today = i['DBSnapshotIdentifier']
    return snapshot_today


def copy_snapshot_other_region(project):
    client = RDS_CLIENT
    client_destiny = RDS_DESTINO

    now = datetime.now()

    copy_name = project + "-" + now.strftime("%Y%m%d") + "-" + now.strftime("%H%M%S")
    copy_arn = get_info_snapshot_rds_today(True)

    try:
        client_destiny.describe_db_snapshots(
            DBSnapshotIdentifier=copy_name
        )
    except:
        response = client_destiny.copy_db_snapshot(
            SourceDBSnapshotIdentifier=copy_arn,
            TargetDBSnapshotIdentifier=copy_name,
            CopyTags=True
        )

    return snapshot_is_ready(copy_name)


def snapshot_is_ready(name_snapshot):
    """
    Snapshot is ready?.
    """
    client_destiny = RDS_DESTINO
    response = client_destiny.describe_db_snapshots(
        DBSnapshotIdentifier=name_snapshot
    )
    snapshot = response['DBSnapshots'][0]
    while(response['DBSnapshots'][0]['Status'] == "pending" or response['DBSnapshots'][0]['Status'] == "creating"):
        response = client_destiny.describe_db_snapshots(
            DBSnapshotIdentifier=name_snapshot
        )
        print("Waiting for snapshot to be available.")
        time.sleep(15)

    print("Snapshot already copied")
    return name_snapshot



def snapshot_rds_up(snapshot_name, new_name_rds):
    """
    Restore snapshot.
    """
    restore_response = RDS_DESTINO.restore_db_instance_from_db_snapshot(
        DBInstanceIdentifier = new_name_rds,
        DBSnapshotIdentifier = snapshot_name,
        DBInstanceClass=INSTANCE_CLASS,
        DBSubnetGroupName=SUBNET_DESTINO
    )
    waiter = RDS_DESTINO.get_waiter('db_instance_available')
    waiter.wait(DBInstanceIdentifier=new_name_rds)
    print( "waiter delay: " + str(waiter.config.delay) )

def delete_rds_backup(name_rds):
    try:
        response = RDS_DESTINO.delete_db_instance(
            DBInstanceIdentifier=name_rds,
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True
        )
        print("Delete " + name_rds + " ok")
    except Exception as e:
        print(e)
        exit(1)

        

def backup_postgres_db(host, database_name, port, user, password, dest_file, verbose):
    """
    Backup postgres db to a file.
    """
    if verbose:
        try:
            process = subprocess.Popen(
                ['pg_dump',
                 '--dbname=postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, database_name),
                 '-Fc',
                 '-f', dest_file,
                 '-v'],
                stdout=subprocess.PIPE
            )
            output = process.communicate()[0]
            if int(process.returncode) != 0:
                print('Command failed. Return code : {}'.format(process.returncode))
                exit(1)
            return output
        except Exception as e:
            print(e)
            exit(1)
    else:

        try:
            process = subprocess.Popen(
                ['pg_dump',
                 '--dbname=postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, database_name),
                 '-f', dest_file],
                stdout=subprocess.PIPE
            )
            output = process.communicate()[0]
            if process.returncode != 0:
                print('Command failed. Return code : {}'.format(process.returncode))
                exit(1)
            return output
        except Exception as e:
            print(e)
            exit(1)


def restore_postgres_db(db_host, db, port, user, password, backup_file, verbose):
    """
    Restore postgres db from a file.
    """
    if verbose:
        try:
            print(user,password,db_host,port, db)
            process = subprocess.Popen(
                ['pg_restore',
                 '--no-owner',
                 '--dbname=postgresql://{}:{}@{}:{}/{}'.format(user,
                                                               password,
                                                               db_host,
                                                               port, db),
                 '-v',
                 backup_file],
                stdout=subprocess.PIPE
            )
            output = process.communicate()[0]
            if int(process.returncode) != 0:
                print('Command failed. Return code : {}'.format(process.returncode))

            return output
        except Exception as e:
            print("Issue with the db restore : {}".format(e))
    else:
        try:
            process = subprocess.Popen(
                ['pg_restore',
                 '--no-owner',
                 '--dbname=postgresql://{}:{}@{}:{}/{}'.format(user,
                                                                      password,
                                                                      db_host,
                                                                      port, db),
                 backup_file],
                stdout=subprocess.PIPE
            )
            output = process.communicate()[0]
            if int(process.returncode) != 0:
                print('Command failed. Return code : {}'.format(process.returncode))

            return output
        except Exception as e:
            print("Issue with the db restore : {}".format(e))


def create_db(db_host, database, db_port, user_name, user_password):
    try:
        con = psycopg2.connect(dbname='postgres', port=db_port,
                               user=user_name, host=db_host,
                               password=user_password)

    except Exception as e:
        print(e)
        exit(1)

    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    try:
        cur.execute("DROP DATABASE {} ;".format(database))
    except Exception as e:
        print('DB does not exist, nothing to drop')
    cur.execute("CREATE DATABASE {} ;".format(database))
    cur.execute("GRANT ALL PRIVILEGES ON DATABASE {} TO {} ;".format(database, user_name))
    return database    


def backup_mysql_db(host, database_name, port, user, password, dest_file, verbose):
    """
    Backup mysql db to a file.
    """
    if verbose:
        try:
            process = subprocess.Popen(
                ['mysqldump',
                 '--host {}'.format(host),
                 '--port {}'.format(port),
                 '--user {}'.format(user),
                 '--password {}'.format(password),
                 '--databases {}'.format(database_name),
                 '--verbose',
                 '>',dest_file],
                stdout=subprocess.PIPE
            )
            output = process.communicate()[0]
            if int(process.returncode) != 0:
                print('Command failed. Return code : {}'.format(process.returncode))
                exit(1)
            return output
        except Exception as e:
            print(e)
            exit(1)
    else:

        try:
            process = subprocess.Popen(
                ['mysqldump',
                 '--host {}'.format(host),
                 '--port {}'.format(port),
                 '--user {}'.format(user),
                 '--password {}'.format(password),
                 '--databases {}'.format(database_name),
                 '>',dest_file],
                stdout=subprocess.PIPE
            )
            output = process.communicate()[0]
            if process.returncode != 0:
                print('Command failed. Return code : {}'.format(process.returncode))
                exit(1)
            return output
        except Exception as e:
            print(e)
            exit(1)       


def upload_to_s3(file_full_path, dest_file):
    """
    Upload a file to an AWS S3 bucket.
    """
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_full_path, AWS_BUCKET_NAME, AWS_BUCKET_PATH + dest_file)
        os.remove(file_full_path)
    except boto3.exceptions.S3UploadFailedError as exc:
        print(exc)
        exit(1)


def download_from_s3(backup_s3_key, dest_file):
    """
    Upload a file to an AWS S3 bucket.
    """
    s3_client = boto3.resource('s3')
    try:
        s3_client.meta.client.download_file(AWS_BUCKET_NAME, backup_s3_key, dest_file)
    except Exception as e:
        print(e)
        exit(1)


def main():
    new_name_rds = "restored-"+ PROJECT + "-" + str(TODAY)
    host_backup = new_name_rds + "." + ID_CUENTA + "." + REGION_DESTINO + ".rds.amazonaws.com"
    # snapshot_name = get_info_snapshot_rds_today(False)
    # print(snapshot_name)
    # snapshot_name = get_info_snapshot_rds_today(True)
    # print(snapshot_name)
    snapshot_name = copy_snapshot_other_region('gds')
    snapshot_rds_up(snapshot_name, new_name_rds)
    backup_postgres_db(host_backup, DB_DATABASE, DB_PORT, DB_USER, DB_PASSWORD, 'dump_', 1)
    delete_rds_backup(new_name_rds)
    create_db(DB_HOST_DESTINO, DB_DATABASE_DESTINO, DB_PORT_DESTINO, DB_USER_DESTINO, DB_PASSWORD_DESTINO)
    restore_postgres_db(DB_HOST_DESTINO, DB_DATABASE_DESTINO, DB_PORT_DESTINO, DB_USER_DESTINO, DB_PASSWORD_DESTINO, '/app/dump_', 1)

    # backup_postgres_db(DB_HOST, DB_DATABASE_CMS, DB_PORT, DB_USER_CMS, DB_PASSWORD_CMS, 'cms_', 1)
    # create_db(DB_HOST_DESTINO, DB_DATABASE_CMS, DB_PORT_DESTINO, DB_USER_DESTINO, DB_PASSWORD_DESTINO)
    # restore_postgres_db(DB_HOST_DESTINO, DB_DATABASE_CMS, DB_PORT_DESTINO, DB_USER_DESTINO, DB_PASSWORD_DESTINO, '/app/cms_', 1)



if __name__ == '__main__':
    main()

