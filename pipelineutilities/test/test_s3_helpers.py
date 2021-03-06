import _set_path  # noqa
import unittest
from unittest.mock import patch, Mock
import boto3
import botocore
from botocore.stub import Stubber
from pipelineutilities.s3_helpers import s3_file_exists, write_s3_file, write_s3_xml, write_s3_json, filedata_is_already_on_s3, md5_checksum, read_s3_file_content, read_s3_json
import datetime
from dateutil.tz import tzutc


class TestS3Helpers(unittest.TestCase):

    @patch('pipelineutilities.s3_helpers.s3_client')
    def test_s3_file_exists_false_when_no_key(self, mock_s3_client):
        """
        s3_file_exists
        Tests that s3_file_exits returns False when there is no file in s3
        Mocks s3_helpers.s3_client - to mock the request
        """
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_client_error('head_object', service_message="message", expected_params={'Bucket': 'bucketnot', 'Key': 'key_not'})

        mock_s3_client.return_value = s3

        with stubber:
            response = s3_file_exists("bucketnot", "key_not")

        self.assertFalse(response)

    @patch('pipelineutilities.s3_helpers.s3_client')
    def test_s3_file_exists_returns_head_object_when_exists(self, mock_s3_client):
        """
        s3_file_exists
        Tests that s3_file_exits returns the head object data when it exists on s3
        Mocks s3_helpers.s3_client - to mock the request
        """
        s3 = boto3.client("s3")
        stubber = Stubber(s3)

        mock_response = {'ResponseMetadata': {'RequestId': '2CA0C8ABC59ED601', 'HostId': 'W81yYPFfh/26bdCJGImLxHYIKQxKIABbu6uLSF8XhuDoPL3gtRsP9x39VyePZeP/XE4C8LHrp6Q=', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amz-id-2': 'W81yYPFfh/26bdCJGImLxHYIKQxKIABbu6uLSF8XhuDoPL3gtRsP9x39VyePZeP/XE4C8LHrp6Q=', 'x-amz-request-id': '2CA0C8ABC59ED601', 'date': 'Wed, 17 Jun 2020 13:28:49 GMT', 'last-modified': 'Wed, 17 Jun 2020 06:08:27 GMT', 'etag': '"f8663bf4e6705bdc617418b690b3e56c"', 'accept-ranges': 'bytes', 'content-type': 'text/json', 'content-length': '50451', 'server': 'AmazonS3'}, 'RetryAttempts': 0}, 'AcceptRanges': 'bytes', 'LastModified': datetime.datetime(2020, 6, 17, 6, 8, 27, tzinfo=tzutc()), 'ContentLength': 50451, 'ETag': '"f8663bf4e6705bdc617418b690b3e56c"', 'ContentType': 'text/json', 'Metadata': {}}  # noqa

        mock_s3_client.return_value = s3
        stubber.add_response('head_object', expected_params={'Bucket': 'bucket', 'Key': 'key'}, service_response=mock_response)

        with stubber:
            response = s3_file_exists("bucket", "key")

        self.assertEqual(response, mock_response)

    @patch('pipelineutilities.s3_helpers.filedata_is_already_on_s3')
    @patch('pipelineutilities.s3_helpers.s3_resource')
    def test_write_s3_file_basic(self, mock_s3_resource, mock_filedata_is_already_on_s3):
        """
        write_s3_file
        Tests that s3 put_object gets called with the basic parameters
        """
        s3 = boto3.resource('s3')
        stubber = Stubber(s3.meta.client)
        mock_response = {'ResponseMetadata': {'RequestId': '2CA0C8ABC59ED601', 'HostId': 'W81yYPFfh/26bdCJGImLxHYIKQxKIABbu6uLSF8XhuDoPL3gtRsP9x39VyePZeP/XE4C8LHrp6Q=', 'HTTPStatusCode': 200}}

        # TEST that it calls put object with the basic params
        stubber.add_response('put_object', expected_params={'Bucket': 'bucket', 'Key': 'key', 'Body': "data"}, service_response=mock_response)

        mock_s3_resource.return_value = s3
        mock_filedata_is_already_on_s3.return_value = False

        with stubber:
            write_s3_file("bucket", "key", "data")

        stubber.assert_no_pending_responses()

    @patch('pipelineutilities.s3_helpers.filedata_is_already_on_s3')
    @patch('pipelineutilities.s3_helpers.s3_resource')
    def test_write_s3_file_complex(self, mock_s3_resource, mock_filedata_is_already_on_s3):
        """
        write_s3_file
        Tests that s3 put_object gets called with passing kwargs to it
        """
        s3 = boto3.resource('s3')
        stubber = Stubber(s3.meta.client)

        mock_response = {'ResponseMetadata': {'RequestId': '2CA0C8ABC59ED601', 'HostId': 'W81yYPFfh/26bdCJGImLxHYIKQxKIABbu6uLSF8XhuDoPL3gtRsP9x39VyePZeP/XE4C8LHrp6Q=', 'HTTPStatusCode': 200}}
        stubber.add_response('put_object', expected_params={'Bucket': 'bucket', 'Key': 'key', 'Body': "data", "ContentType": "contenttype"}, service_response=mock_response)

        mock_s3_resource.return_value = s3
        mock_filedata_is_already_on_s3.return_value = False

        with stubber:
            write_s3_file("bucket", "key", "data", ContentType="contenttype")

        stubber.assert_no_pending_responses()

    @patch('pipelineutilities.s3_helpers.filedata_is_already_on_s3')
    @patch('pipelineutilities.s3_helpers.s3_resource')
    def test_write_s3_file_file_exists(self, mock_s3_resource, mock_filedata_is_already_on_s3):
        """
        write_s3_file
        Tests that s3 put_object does not get called if the file already exists.
        """
        s3 = boto3.resource('s3')
        stubber = Stubber(s3.meta.client)

        mock_filedata_is_already_on_s3.return_value = True
        try:
            with stubber:
                write_s3_file("bucket", "key", "data", ContentType="contenttype")

        except botocore.exceptions.UnStubbedResponseError:
            self.fail("write_s3_file called put_object but it should not have.")

    @patch('pipelineutilities.s3_helpers.write_s3_file')
    def test_write_s3_xml(self, mock_write_s3_file):
        """
        write_s3_xml
        Tests that the correct data is handed off to write_s3_file
        """
        mock_write_s3_file.return_value = None

        write_s3_xml("bucket", "key", "xml")

        mock_write_s3_file.assert_called_once_with("bucket", "key", "xml", ContentType='application/xml')

    @patch('pipelineutilities.s3_helpers.write_s3_file')
    def test_write_s3_json(self, mock_write_s3_file):
        """
        write_s3_json
        Tests that the correct data is handed off to write_s3_file
        """
        mock_write_s3_file.return_value = None

        write_s3_json("bucket", "key", {"json": "json"})

        mock_write_s3_file.assert_called_once_with("bucket", "key", '{"json": "json"}', ContentType="text/json")

    @patch('pipelineutilities.s3_helpers.s3_file_exists')
    @patch('pipelineutilities.s3_helpers.md5_checksum')
    @patch('pipelineutilities.s3_helpers.s3_client')
    def test_filedata_is_already_on_s3_false_if_the_file_does_not_exist(self, mock_s3_client, mock_md5_checksum, mock_s3_file_exists):
        """
        filedata_is_already_on_s3
        Tests that it returns false if the file is not on s3.
        """
        # it is always false no matter if the etag matches.
        mock_s3_file_exists.return_value = False
        self.assertFalse(filedata_is_already_on_s3('bucket', 'key', 'data'))

    @patch('pipelineutilities.s3_helpers.s3_file_exists')
    @patch('pipelineutilities.s3_helpers.md5_checksum')
    @patch('pipelineutilities.s3_helpers.s3_client')
    def test_filedata_is_already_on_s3_true_if_the_etags_match(self, mock_s3_client, mock_md5_checksum, mock_s3_file_exists):
        """
        filedata_is_already_on_s3
        Tests that it returns true if the file is on s3 and the etags match
        """
        mock_s3_file_exists.return_value = {'ETag': '"etag"'}
        mock_md5_checksum.return_value = 'etag'

        self.assertTrue(filedata_is_already_on_s3('bucket', 'key', 'data'))

    @patch('pipelineutilities.s3_helpers.s3_file_exists')
    @patch('pipelineutilities.s3_helpers.md5_checksum')
    @patch('pipelineutilities.s3_helpers.s3_client')
    def test_filedata_is_already_on_s3_false_if_the_etags_do_not_match(self, mock_s3_client, mock_md5_checksum, mock_s3_file_exists):
        """
        filedata_is_already_on_s3
        Tests that it returns false if the file is on s3 but the etags do not match
        """
        mock_s3_file_exists.return_value = {'ETag': '"etag"'}
        mock_md5_checksum.return_value = 'new_etag'

        self.assertFalse(filedata_is_already_on_s3('bucket', 'key', 'data'))

    def test_md5_checksum_does_hex_md5(self):
        """
        md5_checksum
        Tests that it returns the correct checksum value
        """
        result = "098f6bcd4621d373cade4e832627b4f6"
        self.assertEqual(result, md5_checksum("test"))

    @patch('pipelineutilities.s3_helpers.s3_resource')
    def test_read_s3_file_content_exists(self, mock_s3_resource):
        """
        read_s3_file_content
        Tests that s3 file is read correctly
        """
        body_mock = Mock()
        body_mock.read.return_value.decode.return_value = "body"

        s3 = boto3.resource('s3')
        stubber = Stubber(s3.meta.client)

        mock_response = {'Body': body_mock, 'ResponseMetadata': {'RequestId': '2CA0C8ABC59ED601', 'HostId': 'W81yYPFfh/26bdCJGImLxHYIKQxKIABbu6uLSF8XhuDoPL3gtRsP9x39VyePZeP/XE4C8LHrp6Q=', 'HTTPStatusCode': 200}}
        stubber.add_response('get_object', expected_params={'Bucket': 'bucket', 'Key': 'key'}, service_response=mock_response)

        mock_s3_resource.return_value = s3

        with stubber:
            content = read_s3_file_content("bucket", "key")

        self.assertEqual('body', content)
        stubber.assert_no_pending_responses()

    @patch('pipelineutilities.s3_helpers.s3_resource')
    def test_read_s3_file_content_does_not_exists(self, mock_s3_resource):
        """
        read_s3_file_content
        Tests that it returns "" when the object does not exist
        """
        s3 = boto3.resource('s3')
        stubber = Stubber(s3.meta.client)
        stubber.add_client_error('get_object', service_message="message", expected_params={'Bucket': 'bucketnot', 'Key': 'key_not'})

        mock_s3_resource.return_value = s3

        with stubber:
            content = read_s3_file_content("bucketnot", "key_not")

        self.assertEqual("", content)
        stubber.assert_no_pending_responses()

    @patch('pipelineutilities.s3_helpers.read_s3_file_content')
    def test_read_s3_json(self, mock_read_s3_file_content):
        """
        read_s3_json
        Tests that the json as a hash is returned.
        """
        mock_read_s3_file_content.return_value = '{"json": "json"}'

        content = read_s3_json("bucket", "key")

        mock_read_s3_file_content.assert_called_once_with("bucket", "key")
        self.assertEqual({"json": "json"}, content)

    @patch('pipelineutilities.s3_helpers.read_s3_file_content')
    def test_read_s3_json_empty(self, mock_read_s3_file_content):
        """
        read_s3_json
        Tests that an empty file becomes and empty dict
        """
        mock_read_s3_file_content.return_value = ''

        content = read_s3_json("bucket", "key")

        mock_read_s3_file_content.assert_called_once_with("bucket", "key")
        self.assertEqual({}, content)
