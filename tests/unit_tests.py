import os
import sys

os.environ['TESTING'] = "true"

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "../"))
sys.path.append(os.path.join(here, "../sys_packages"))

from mock import patch
from handler import sign, get_signature_key, create_aws_headers, initialize, upload, aggregate


def setup_function(function):
    """Setup Function..."""

    return


@patch('hmac.new')
def test_sign_unit(hmac_new_mock):
    """Test the sign() function."""

    hmac_new_mock.return_value.digest.return_value = "test2"

    return_val = sign("test3", "test4")

    assert 'test2' in return_val


@patch('handler.sign')
def test_get_signature_key_unit(mock_sign):
    """Test the get_signature_key() function."""
    key = 'test1'
    date_stamp = 'test2'
    region_name = 'us-east-1'
    service_name = 'es'

    mock_sign.return_value = "test3"

    return_val = get_signature_key(key, date_stamp, region_name, service_name)

    assert 'test3' in return_val


@patch('requests.put')
def test_initialize_unit(requests_put_mock):
    """Test the initialize() function."""
    event = {}
    context = {}

    requests_put_mock.return_value.text = "test1"

    return_val = initialize(event, context)

    assert 'test1' in return_val['body']


@patch('requests.post')
def test_aggregate_non200_unit(requests_post_mock):
    """Test the aggregate() function when ElasticSearch returns a non-200 message."""
    event = {
        'body': '{"aggregations": "stats","field": "cti.num_agents"}'
    }
    context = {}

    requests_post_mock.return_value.text = '{"test": "test1"}'
    requests_post_mock.return_value.status_code = 300

    return_val = aggregate(event, context)

    assert return_val['statusCode'] == 300
    assert '{"test": "test1"}' in return_val['body']


@patch('requests.post')
def test_aggregate_200_unit(requests_post_mock):
    """Test the aggregate() function when ElasticSearch returns a 200 message."""
    event = {
        'body': '{"aggregations": "stats","field": "cti.num_agents"}'
    }
    context = {}

    requests_post_mock.return_value.text = '{"aggregations": {"data_aggregates": {"test": "test1"}}}'
    requests_post_mock.return_value.status_code = 200

    return_val = aggregate(event, context)

    assert return_val['statusCode'] == 200
    assert '{"test": "test1"}' in return_val['body']