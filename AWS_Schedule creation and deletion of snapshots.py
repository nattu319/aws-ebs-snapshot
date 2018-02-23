# Schedule creation and deletion of snapshots.
# py3.6
import boto3
import time, datetime
from datetime import datetime, timedelta

def lambda_handler(event, context):
    
    # test loop 
    start_backup = 'yes'
    start_delete = 'no'
    
    # Settings
    ec = boto3.client('ec2')
    iam = boto3.client('iam')
    reg = 'ap-northeast-2'
    # Get list of regions
    regions = ec.describe_regions().get('Regions')

    # Iterate over regions
    if start_backup == 'yes' :

        for region in regions:
            
            reg_now = region['RegionName']
            
            if (reg_now == reg):
                # List
                print ("Checking region %s " % region['RegionName'])
        
                # Connect to region
                reg=region['RegionName']
                ec = boto3.client('ec2', region_name=reg)
            
                # Get all in-use volumes in all regions
                result = ec.describe_volumes( Filters=[{'Name': 'status', 'Values': ['in-use']}])
        
                for volume in result['Volumes']:
                    print ("Backing up %s in %s" % (volume['VolumeId'], volume['AvailabilityZone']))
                
                    # Create snapshot
                    result = ec.create_snapshot(VolumeId=volume['VolumeId'],Description='Created by Lambda backup function ebs-snapshot')
                
                    # Get snapshot resource 
                    ec2resource = boto3.resource('ec2', region_name=reg)
                    snapshot = ec2resource.Snapshot(result['SnapshotId'])
                    volumename = 'N/A'
                
                    # Find name tag for volume if it exists
                    if 'Tags' in volume:
                        for tags in volume['Tags']:
                            if tags["Key"] == 'Name':
                                volumename = tags["Value"]
                
                    # Add volume name to snapshot for easier identification
                    snapshot.create_tags(Tags=[{'Key': 'Name','Value': volumename}])
    else:
        print ('Stop backup')
    
    if start_delete == 'yes' :
        
        # settings
        ec2resource = boto3.resource('ec2', region_name=reg)
        days = 7
        
        # timeLimit
        d = datetime.now() - timedelta(days=days)
        timeLimit = datetime(d.year,d.month,d.day)
        print ('Deleting any snapshots older than {days} days'.format(days=days))

        # filter tag
        filters = [
            {'Name': 'tag-key', 'Values': ['Name']},
            {'Name': 'tag-value', 'Values': ['vm-tag']},
        ]
        
        snapshot_response = ec.describe_snapshots(Filters=filters)
        for snapshot in snapshot_response['Snapshots']:
            d = (snapshot['StartTime'])
            snapshot_time = datetime(d.year,d.month,d.day)
            if (snapshot_time < timeLimit):
                print ("Deleting snapshot %s" % snap['SnapshotId'])
                ec.delete_snapshot(SnapshotId=snap['SnapshotId'])
            else:
                print ('Stop deletion')
                
    else:
        print ('Stop deletion')
