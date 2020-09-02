import boto3
import click
import botocore

session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

def filter_instances(project):
    instances = []
    if project:
        filters = [{'Name':'tag:Project', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

@click.group()
def cli():
    """Shotty manages the snapshot"""

@cli.group('snapshots')
def snapshots():
    """"Commands for Snapshots"""

@snapshots.command('list')
@click.option('--project', default=None,
    help="Only Snapshots for project(tag Project:<name>)")
@click.option('--all', 'list_all', default=False, is_flag=True,
    help="List all snapshots for each volume, not just the most recent one")
def list_snapshots(project,list_all):
    "List Snapshot of EBS Volumes"
    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(",".join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                  )))
                if s.state == 'completed' and not list_all: break
    return

@cli.group('volumes')
def volumes():
    """"Commands for Volumes"""

@volumes.command('list')
@click.option('--project', default=None,
    help="Only Volumes for project(tag Project:<name>)")

def list_volumes(project):
    "List Volumes attached to EC2 Instances"
    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            print(",".join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted"
            )))
    return

@cli.group('instances')
def instances():
    """"Commands for instances"""

@instances.command('snapshot',
   help="Create snapshots of all Volumes of EC2 instance")
@click.option('--project', default=None,
    help="Only instances for project(tag Project:<name>)")
def create_snapshot(project):
    "Create snapshot of EC2 Instances"

    instances = filter_instances(project)

    for i in instances:
        print("Stopping EC2 instance: {0}".format(i.id))

        i.stop()
        i.wait_until_stopped()

        for v in i.volumes.all():
            print("Creating Snapshot of EC2-instance: {0}  Volume: {1}".format(i.id,v.id))
            v.create_snapshot(Description="Created by SnashotAlyzer")

        print("Starting EC2 instance: {0}".format(i.id))

        i.start()
        i.wait_until_running()
    print("Job's done!!")
    return

@instances.command('list')
@click.option('--project', default=None,
    help="Only instances for project(tag Project:<name>)")
def list_instances(project):
    "List EC2 Instances"

    instances = filter_instances(project)

    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or []}
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<no project>'))))
    return

@instances.command('stop')
@click.option('--project', default=None,
    help="Only instances for project(tag Project:<name>)")
def stop_instances(project):
    "Stopping EC2 instances"

    instances = filter_instances(project)

    for i in instances:
        print("Stopping instance : {0}".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
             print(" Could not stop EC2-instance : {0}  .".format(i.id) + str(e))
             continue

    return

@instances.command('start')
@click.option('--project', default=None,
    help="Only instances for project(tag Project:<name>)")
def start_instances(project):
    "Starting EC2 instances"

    instances = filter_instances(project)

    for i in instances:
        print("Starting instance : {0}".format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
             print(" Could not start EC2-instance : {0}  .".format(i.id) + str(e))
             continue

    return

if __name__ == '__main__':
    cli()
