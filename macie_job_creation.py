import argparse
import boto3
import os
import botocore.exceptions
import json
from datetime import date

# Globals
client = boto3.client('macie2')


# validate path to file
def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise FileNotFoundError(string)

#Creates filters and validates cmd line arguments
def filter_args():
    my_parser = argparse.ArgumentParser()
    group = my_parser.add_mutually_exclusive_group(required=True)
    my_parser.add_argument('--frequency', action='store', type=str, required=True, choices=['ONE_TIME', 'SCHEDULED'], help= 'Set a frequency for the sensitive discovery job to run')
    my_parser.add_argument('--account_id', action='store', type=str, required=True, help='Account ID where the S3 Buckets Reside')
    group.add_argument('--s3_tags', action='store', type=file_path, help= 'Provide a path to a json file in the form: [{"Key": "ExampleKey"}, {"Value": "ExampleValue"}].  Multiple tags supported')
    group.add_argument('--path', action='store', type=file_path, help='local path to a list of buckets, with each bucket on a new line')
    group.add_argument('--bucketlist', action='store', nargs='+') 
    args = my_parser.parse_args()
    return args

'''
Iterates through all Buckets that Macie can view, and return a list of buckets to enable Macie jobs if at least one of the tags is present, and the account_id of the bucket correlates with the argument supplied.
Inputs: 
tag_dict: Type Dict
          Dictionary of Tag Keys/Values to check S3 Buckets against.  Jobs will be enabled in the event they are present

Ouputs: 
buckets_to_enable: Type: List
                   List of S3 Buckets names. 
'''
def discover_buckets(tag_dict,args): 
    bucket_list = client.describe_buckets()['buckets']
    buckets_to_enable = []
    for bucket in bucket_list:
        if bucket['accountId'] == str(args.account_id):
            try:
                tags = bucket['tags']
                for keypair in tag_dict: 
                    tagged_bucket = [bucket['bucketName'] for tag in tags if tag['key'] == keypair['Key'] and tag['value'] == keypair['Value']]
                    if len(tagged_bucket) != 0:
                        print(f"Found Tag: {keypair}, on bucket: {tagged_bucket[0]}")
                        buckets_to_enable.append(tagged_bucket[0])
                        break    
            except client.exceptions.ClientError: 
                print(f"No tags found on {bucket['Name']}")
        else: 
            print(f"Bucket Account ID of {bucket['bucketName']} ({bucket['accountId']}) does not correlate with supplied account_id ({args.account_id})")
        
    return buckets_to_enable


''' 
Accepts the buckets to enable input, and cycles through each of the buckets and attempts to create a Macie Job.  Returns a dictionary detailing the names of success and failures.
Inputs: 
buckets_to_enable: Type: List
                   List of S3 Buckets names.
args: Type: List
      Command line arguments provided by User

Ouputs: 
Return: Type: Dict
        Dictionary of list of successes and failures of Macie job configuration

'''
def create_discovery_job(buckets_to_enable, args):
    tag_dict = {
                'script_created': "True",
                }
    job_frequency = args.frequency
    enabled = []
    errored = []
    today = date.today()
    d1 = today.strftime("%d-%m")
    for i in buckets_to_enable:
        try:
            response = client.create_classification_job(description=f"Automated discovery job for {i}",
                    initialRun=True,
                    jobType=job_frequency,
                    name= f"{i}_{d1}_{job_frequency}",
                    s3JobDefinition= {
                    'bucketDefinitions': [{
                        'accountId': args.account_id,
                        'buckets': [i]
                    }]    
                    },
                    tags = tag_dict 
                    )
            if str(response['ResponseMetadata']['HTTPStatusCode']) == '200':
                print(f'Job successfully created for: {i}')
                print(f"Job ARN: {response['jobArn']}")
                enabled.append(i)

        except client.exceptions.ValidationException as error:
            print(f"Check inputs and parameters: {error}")
            errored.append(i)

        except Exception as e: 
            print(f'Error found: {e}')
            errored.append(i)

    return {
        "Macie enabled Buckets": enabled,
        "Errors occured on Buckets": errored
    }


if __name__ == '__main__':
    # #Validate mandatory args are present
    args = filter_args()

    # # Read in path from args
    if args.path:
        bucketarray = [] 
        with open(args.path, 'r') as reader: 
            for line in reader: 
                bucketarray.append(line.strip('\n'))
        buckets_to_enable = bucketarray

    if args.bucketlist:
        buckets_to_enable = args.bucketlist

    # #load from json file, and discover buckets that conform to the designated tags. 
    if args.s3_tags:
        with open(args.s3_tags, 'r') as reader: 
            tag_dict = json.load(reader)
            buckets_to_enable = discover_buckets(tag_dict,args)

    print(f"Buckets to enable: {buckets_to_enable}")    

    # Create jobs from inputted list. 
    creation_results = create_discovery_job(buckets_to_enable, args)
    print(creation_results)