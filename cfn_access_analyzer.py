import boto3
import json
import os
from cfn_flip import to_json
import argparse
import retry
import botocore

access_client = boto3.client('accessanalyzer')
iam_client = boto3.client('iam')
sts_client = boto3.client('sts')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to the cfn template to analyse")
    return parser.parse_args()


def parse_cfn(policy_array, account_id, region):
    for policy in policy_array:
        for x in policy['PolicyDocument']['Statement']:
            if type(x['Resource']) == list:
                for i, rsc in enumerate(x['Resource']):
                    if type(rsc) == dict and list(rsc.keys())[0] == 'Fn::Sub':
                        x['Resource'][i] = list(rsc.values())[0].replace("${AWS::AccountId}", account_id)
                        x['Resource'][i] = x['Resource'][i].replace("${AWS::Region}", region)
            
            elif type(x['Resource']) == dict and list(x['Resource'].keys())[0] == 'Fn::Sub':
                x['Resource'] = list(x['Resource'].values())[0].replace("${AWS::AccountId}", account_id)
                x['Resource']= [i].replace("${AWS::Region}", region)

            ##Conditions
            if x.get('Condition', '') != '': 
                for i, block in enumerate(x['Condition']): 
                    for p, cond in enumerate(x['Condition'][block].keys()):
                        try:
                            if type(x['Condition'][block][cond]) == list:
                                for k, statement in enumerate(x['Condition'][block][cond]):
                                    if type(statement) == dict and list(statement.keys())[0] == 'Fn::Sub':
                                        x['Condition'][block][cond][k] = list(statement.values())[0].replace("${AWS::AccountId}", account_id)
                                        x['Condition'][block][cond][k] = x['Condition'][block][cond][k].replace("${AWS::Region}", region)
                            
                            # To DO: Implement parameter support
                            # elif type(list(x['Condition'][block][cond].keys())[0])== str and list(x['Condition'][block][cond].keys())[0] == 'Ref':
                            #  x[Çondition'][block][cond] == variable

                            elif type(list(x['Condition'][block][cond].keys())[0])== str and list(x['Condition'][block][cond].keys())[0] == 'Fn::Sub':
                                x['Condition'][block][cond] == list(x['Condition'][block][cond].values())[0].replace("${AWS::AccountId}", account_id)
                                x['Condition'][block][cond] == x['Condition'][block][cond].replace("${AWS::Region}", region)
                        
                        except AttributeError:
                            print('Condition does not require parsing')
        return policy_array


def validate_policy(policy_array):
    for policy in policy_array:
        print(f'Analysing: {policy["PolicyName"]}')
        try:
            response = retry.api.retry_call(
                access_client.validate_policy,
                fkwargs={"locale": 'EN', "policyDocument": json.dumps(policy['PolicyDocument']), 'policyType': 'IDENTITY_POLICY'},
                jitter=5,
                tries=5,
                backoff=1.5,
                max_delay=60,
                exceptions=botocore.exceptions.ClientError
            )
            findings = response['findings']
            if len(findings) > 0:
                print(findings)
            else:
                print(f"No findings found for {policy['PolicyName']}")
                print('\n')
        
        except access_client.exceptions.InternalServerException: 
            print(f"Failed to validate {policy['PolicyName']}")
            print('\n')
            next


if __name__ == '__main__':
    args = parse_args()

    account_id = sts_client.get_caller_identity()['Account']

    region = os.getenv("REGION")
    # To do: #Read in parameter file, and be able to parse in Ref functions based off it
    path = args.path
    try:
        with open(path, 'r') as document: 
            cfn_template = json.loads(to_json(document.read()))
            Resources = cfn_template['Resources']

            policy_array = [{'PolicyName': policy, 'PolicyDocument': Resources[policy]['Properties']['PolicyDocument']} for policy
                in Resources.keys() if Resources[policy]['Type'] == 'AWS::IAM::ManagedPolicy']
            
            for policy in Resources.keys():
                if Resources[policy]['Type'] == 'AWS::IAM::Role':
                    for Policy in Resources[policy]['Properties']['Policies']:
                        
                        policy_array.append({
                            'PolicyName': Policy['PolicyName'],
                            'PolicyDocument': Policy['PolicyDocument'],
                        })
            
            parse_policy_array = parse_cfn(policy_array, account_id, region)
            validate_policy(policy_array)
    
    except FileNotFoundError as e:
        print(f"Error when trying to locate path.  Check Path and try again.")
        raise(e)