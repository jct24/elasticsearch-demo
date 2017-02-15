from __future__ import print_function

import json
import sys
import os
from base64 import b64decode

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "sys_packages"))

import requests
import datetime
import hashlib
import hmac
import boto3

# AWS Access key and Secret key are stored as Lambda Env variables.
# See the README.md for more information about creating these variables.
encrypted_access_key = os.environ.get('AWS_ACCESS_KEY_ES')
encrypted_secret_key = os.environ.get('AWS_SECRET_KEY_ES')

access_key = boto3.client('kms').decrypt(CiphertextBlob=b64decode(encrypted_access_key))['Plaintext']
secret_key = boto3.client('kms').decrypt(CiphertextBlob=b64decode(encrypted_secret_key))['Plaintext']

s3 = boto3.client('s3')

host = 'search-elasticsearch-demo-yag6jaozzuwerhu2yv4l4nthii.us-east-1.es.amazonaws.com'


def sign(key, msg):
    """Create HMAC digest with SHA256 for use in an AWS Signed URL.

    Signed URL code taken from AWS docs and adapted for this script
    http://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html

    Args:
        key: Key used to calculate HMAC digest.
        msg: Message used to calculate HMAC digest.

    Returns:
        string: SHA-256 encoded HMAC digest.

    """

    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def get_signature_key(key, date_stamp, region_name, service_name):
    """Create message signature for use in an AWS Signed URL.

    Signed URL code taken from AWS docs and adapted for this script
    http://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html

    Args:
        key: AWS secret key used to calculate signature.
        date_stamp: Current date stamp created using t.strftime('%Y%m%d').
        region_name: AWS region.
        service_name: Name of the AWS service to be called.

    Returns:
        string: Signed signature to be used in an AWS signed URL.

    """

    k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, 'aws4_request')
    return k_signing


def create_aws_headers(data, uri, method):
    """Create AWS signed uri headers for use in an AWS Signed URL.

    Signed URL code taken from AWS docs and adapted for this script
    http://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html

    Args:
        data: Message that needs to be signed.
        uri: Uri of the api call (ie. '/data/')
        method: HTTP method that will be used (ie. 'POST', 'PUT', 'GET', etc)

    Returns:
        dict: Header object containing the 'Content-Type', 'X-Amz-Date' and 'Authorization'.

    """

    content_type = 'application/x-amz-json-1.0'
    region = 'us-east-1'

    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
    canonical_querystring = ''

    canonical_headers = 'content-type:' + content_type + '\n' + \
                        'host:' + host + '\n' + \
                        'x-amz-date:' + amz_date + '\n'

    signed_headers = 'content-type;host;x-amz-date'
    payload_hash = hashlib.sha256(data).hexdigest()

    canonical_request = method + '\n' + \
                        uri + '\n' + \
                        canonical_querystring + '\n' + \
                        canonical_headers + '\n' + \
                        signed_headers + '\n' + \
                        payload_hash

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + region + '/es/' + 'aws4_request'

    string_to_sign = algorithm + '\n' + \
                     amz_date + '\n' + \
                     credential_scope + '\n' + \
                     hashlib.sha256(canonical_request).hexdigest()

    signing_key = get_signature_key(secret_key, date_stamp, region, 'es')
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    authorization_header = algorithm + ' ' + \
                           'Credential=' + access_key + '/' + credential_scope + ', ' + \
                           'SignedHeaders=' + signed_headers + ', ' + \
                           'Signature=' + signature

    headers = {'Content-Type': content_type,
               'X-Amz-Date': amz_date,
               'Authorization': authorization_header}

    return headers


def initialize(event, context):
    """Initialize the ElasticSearch cluster.  This function is used to initialize the ElasticSearch cluster.  Currently
    the only thing that's being set is "numeric_detection", which is set to enable ES to convert a quoted number
    (ie: "10") into a number instead of storing it as a string.  This enables aggregations over fields that are
    incorrectly formatted as strings but are really numbers.

    Example:
        curl "[ServiceEndpoint]/initialize"

    Args:
        event: AWS Lambda uses this parameter to pass in event data to the handler.
        context: AWS Lambda uses this parameter to provide runtime information to your handler.

    Returns:
        dict: The return response returns a 200 on success along with the return text from ElasticSearch.

    """

    url = 'https://' + host

    numeric_detection_uri = "/data/"

    numeric_detection = {
      "mappings": {
        "event": {
          "numeric_detection": "true"
        }
      }
    }

    headers = create_aws_headers(json.dumps(numeric_detection), numeric_detection_uri, 'PUT')

    req = requests.put(url + numeric_detection_uri, data=json.dumps(numeric_detection), headers=headers)

    print("Req: " + req.text)

    response = {
        "statusCode": 200,
        "body": req.text
    }

    return response


def upload(event, context):
    """Upload a JSON formatted file to be loaded into the ElasticSearch cluster.  This function is never called
    directly.  Instead it's triggered off an upload into the data S3 bucket.

    Example:
        aws s3 cp data.json s3://elasticsearchdemo-data/data.json

    Args:
        event: AWS Lambda uses this parameter to pass in event data to the handler.
        context: AWS Lambda uses this parameter to provide runtime information to your handler.

    Returns:
        dict: The return response returns a 200 on success.

    """

    # S3 bucket and file name/path
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    file_path = '/tmp/data.json'

    # Downloads file from S3 to above path.
    s3.download_file(bucket, key, file_path)

    url = 'https://' + host

    event_uri = '/data/event/'

    # Sends each line of the JSON file to ElasticSearch using AWS Signed URLs
    with open(file_path, 'r') as file:
        for data in file:
            headers = create_aws_headers(data, event_uri, 'POST')

            req = requests.post(url + event_uri, data=data, headers=headers)

            # If status code is not successful, retry 3 more times.
            retry_counter = 1
            while req.status_code != 201 and retry_counter < 4:
                print("retry " +
                      str(retry_counter) +
                      " of 3 - failed sending data to elasticsearch: " +
                      str(req.status_code) +
                      "\nReq: " +
                      req.text)

                req = requests.post(url + event_uri, data=data, headers=headers)

                retry_counter += 1

            print("Returned text: " + req.text)

    response = {
        "statusCode": 200,
        "body": "Your function executed successfully!"
    }

    return response


def aggregate(event, context):
    """Return an aggregate value from a database field.

    Example:
        curl -XPOST "[ServiceEndpoint]/aggregate" -d'
        {
            "aggregations": "stats",
            "field": "cti.num_agents"
        }'

    Args:
        event: AWS Lambda uses this parameter to pass in event data to the handler.
        context: AWS Lambda uses this parameter to provide runtime information to your handler.

    Returns:
        On success: dict: The return response returns a 200 and the aggregate value/s on success.
        On error: dict: The return response returns the status code returned by ElasticSearch along with the
            ElasticSearch response text.

    """

    agg = {
        "size": 0,
        "aggs": {
            "data_aggregates": {
                json.loads(event['body'])['aggregations']: {
                    "field": json.loads(event['body'])['field']
                }
            }
        }
    }

    ret = requests.post('https://' + host + "/data/event/_search", data=json.dumps(agg))

    if ret.status_code == 200:
        body = json.dumps(json.loads(ret.text)['aggregations']['data_aggregates'])
    else:
        body = ret.text

    response = {
        "statusCode": ret.status_code,
        "body": body
    }

    return response
