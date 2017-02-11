### To install new dependencies into the project:
```
pip install -t sys_packages/ -r requirements.txt
```

### To setup stack:
- Setup the AWS Lambda keys
  - Create an IAM user 'es-user' with no permissions, save the secret
    and access keys for later.
  - Create a KMS key using the following policy as an example:
    ```
        {
          "Version": "2012-10-17",
          "Id": "key-consolepolicy-2",
          "Statement": [
            {
              "Sid": "Enable IAM User Permissions",
              "Effect": "Allow",
              "Principal": {
                "AWS": "arn:aws:iam::500402628989:root"
              },
              "Action": "kms:*",
              "Resource": "*"
            },
            {
              "Sid": "Allow access for Key Administrators",
              "Effect": "Allow",
              "Principal": {
                "AWS": [
                  "arn:aws:iam::500402628989:user/es-user",
                  "arn:aws:iam::500402628989:role/elasticsearchdemo-aws-dev-us-east-1-lambdaRole"
                ]
              },
              "Action": [
                "kms:Create*",
                "kms:Describe*",
                "kms:Enable*",
                "kms:List*",
                "kms:Put*",
                "kms:Update*",
                "kms:Revoke*",
                "kms:Disable*",
                "kms:Get*",
                "kms:Delete*",
                "kms:ScheduleKeyDeletion",
                "kms:CancelKeyDeletion"
              ],
              "Resource": "*"
            },
            {
              "Sid": "Allow use of the key",
              "Effect": "Allow",
              "Principal": {
                "AWS": [
                  "arn:aws:iam::500402628989:user/es-user",
                  "arn:aws:iam::500402628989:role/elasticsearchdemo-aws-dev-us-east-1-lambdaRole"
                ]
              },
              "Action": [
                "kms:Encrypt",
                "kms:Decrypt",
                "kms:ReEncrypt*",
                "kms:GenerateDataKey*",
                "kms:DescribeKey"
              ],
              "Resource": "*"
            },
            {
              "Sid": "Allow attachment of persistent resources",
              "Effect": "Allow",
              "Principal": {
                "AWS": [
                  "arn:aws:iam::500402628989:user/es-user",
                  "arn:aws:iam::500402628989:role/elasticsearchdemo-aws-dev-us-east-1-lambdaRole"
                ]
              },
              "Action": [
                "kms:CreateGrant",
                "kms:ListGrants",
                "kms:RevokeGrant"
              ],
              "Resource": "*",
              "Condition": {
                "Bool": {
                  "kms:GrantIsForAWSResource": "true"
                }
              }
            }
          ]
        }
      ```
  - Use the KMS Key to encrypt the Access and Secret keys saved from 'es-user'
    ```
    aws kms encrypt --key-id [kms_key_id] --plaintext [secret/access_key] --output text --query CiphertextBlob | base64 --decode
    ```
  - Update the following variables in serverless.yml
    - AWS_ACCESS_KEY_ES
    - AWS_SECRET_KEY_ES
- Run this serverless command to deploy stack
```
serverless deploy -v
```

### Initialize:
```
curl "[ServiceEndpoint]/initialize"
```

### Example to upload data:
```
aws s3 cp data.json s3://elasticsearchdemo-data/data.json
```

### Example to query for aggregate:
```
curl -XPOST "[ServiceEndpoint]/aggregate" -d'
{
    "aggregations": "stats",
    "field": "cti.num_agents"
}'
```
Possible aggregations can include; min, max, sum, avg, stats, extended_stats, value_count, etc.
See [ElasticSearch Aggregations](https://www.elastic.co/guide/en/elasticsearch/reference/1.5/search-aggregations.html)
for more information.

### To remove stack:
- First delete all objects from the S3 data bucket
- Run this serverless command to remove stack
```
serverless remove
```