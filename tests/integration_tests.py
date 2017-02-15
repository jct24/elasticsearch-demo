import os
import sys
import json

os.environ['TESTING'] = "true"

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "../"))
sys.path.append(os.path.join(here, "../sys_packages"))

from handler import sign, get_signature_key, create_aws_headers, initialize, upload, aggregate


def setup_function(function):
    """Setup Function..."""


def test_sign_int():
    """Test the sign() function."""
    msg = "test1"
    key = "test2"
    output = sign(key, msg)

    assert output == '\\>*\xc1\xfbS\xee\x84\x0c\xd7\xe7\xca\x1c\x1d\xf1\xe2\xde|\x11\x95\xcaG(\xeb\xb2"i\x9e\x9c6w\xfd'


def test_get_signature_key_int():
    """Test the get_signature_key() function."""
    key = 'test'
    date_stamp = 'test'
    region_name = 'us-east-1'
    service_name = 'es'

    output = get_signature_key(key, date_stamp, region_name, service_name)

    assert output == "oWI'\xdf\xaelx\xee\xb3\x1ft \x01l\xa2\xbfz\x1eP^\x13\x0e\xe5\x08\x8e\\\x12x\xearU"


def test_create_aws_headers_int():
    """Test the 'Content-Type' return of the create_headers() function."""
    data = "test"
    uri = "/test1/"
    method = "POST"

    output = create_aws_headers(data, uri, method)

    expected_output = {
        'Content-Type': 'application/x-amz-json-1.0'
    }

    assert output['Content-Type'] == expected_output['Content-Type']