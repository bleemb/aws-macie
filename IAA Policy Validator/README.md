# IAA Policy Validator

### Purpose
This purpose of this script is to parse cloudformation code, execute the IAM Access Analyser Policy validator,
and return the findings in various formats.
https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-validation.html

### Command line arguments:
--path: Path to the cloudformation template to analyse
Required: Yes
Type: string (valid file path)

--output: Elect to return the output of the validator, either through cli or to a json file
Required: No
Type: Selection, choices=['print', 'file']

#### Example Usage
1. Path to a json cloudformation template.  Script assertion will fail if any findings are returned
python cfn_access_analyzer.py --path ../sample_cfn.json

2.  Path to a yaml cloudformation template, outputting a results.json file
python cfn_access_analyzer.py --path sample_cfn.yaml --output file

3. Path to a yaml cloudformation template, printing results
python cfn_access_analyzer.py --path sample_cfn.yaml --output print