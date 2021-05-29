# IAA Policy Validator

### Purpose
This purpose of this script is to parse cloudformation code, execute the [IAM Access Analyser Policy validator](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-validation.html),
and return the findings in various formats.

<br>  

### Requirements
- IAM role/user with `access-analyzer:ValidatePolicy` IAM permission
- Script dependencies installed

<br> 

### Command line arguments:
``--path``:  
Path to the cloudformation template to analyse  
**Required**: Yes  
**Type**: string (valid file path)  
**Example**: sample_cfn.yaml

``--output``:  
Elect to return the output of the validator, either through cli or to a json file  
**Required**: No  
**Type**: Selection, choices=print | file  
**Example**: print

``--ignore_finding_types``:  
Selectively ignore Policy Validator finding types.  Supplied variable must exactly match finding type returned from API call  
**Required**: No  
**Type**: Comma seperated strings, choices= ERROR | SECURITY_WARNING | SUGGESTION | WARNING  
**Example**: WARNING, SUGGESTION  
**NOTE**: An extensive list of findings can be found [here](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-reference-policy-checks.html).

<br>  

### Example Usage
1. Path to a json cloudformation template.  Script assertion will fail if any findings are returned  
``python cfn_access_analyzer.py --path ../sample_cfn.json``

2.  Path to a yaml cloudformation template, outputting a results.json file  
`python cfn_access_analyzer.py --path sample_cfn.yaml --output file`

3. Print results to console   
`python cfn_access_analyzer.py --path sample_cfn.yaml --output print` 

3. Selectively ignore all WARNING and SUGGESTION findings   
`python cfn_access_analyzer.py --path sample_cfn.yaml --ignore_finding_types WARNING, SUGGESTION` 

<br> 

### Feature Backlog
- More granular finding type filtering
- Scanning of multiple files with one execution
- Import parameter config file, and input values into cfn