#!/usr/bin/python3
"""This module converts images to pyramid tiffs using libvips."""

import sys
import json
import boto3
from s3_helpers import upload_json
from processor_factory import ProcessorFactory
from load_standard_json import load_standard_json
from pipeline_config import load_pipeline_config


class ImageRunner():
    def __init__(self, config: dict) -> None:
        self.ids = config['ids']
        self.bucket = config['process-bucket']
        self.img_write_base = config['process-bucket-read-basepath']
        self.img_file = config['image-data-file']
        self.gdrive_ssm = f"{config['google_keys_ssm_base']}/credentials"
        self.config = config
        self.processor = None

    def process_images(self) -> None:
        for id in self.ids:
            print("----------finished:", id)
            id_results = {}
            num = 1
            for file in load_standard_json(id, self.config).files():
                print(num)
                num = num + 1

                if not self.processor:
                    self._set_processor(file)
                img_config = {
                    'collection_id': id,
                    'bucket': self.bucket,
                    'img_write_base': self.img_write_base
                }

                if self._can_process_file(file):
                    self.processor.set_data(file, img_config)
                    id_results.update(self.processor.process())
            s3_file = f"{self.img_write_base}/{id}/{self.img_file}"
            upload_json(self.bucket, s3_file, id_results)

    def _can_process_file(self, file):
        return not file.get("mimeType", "") == "application/xml"

    def _get_processor_info(self, filepath: str) -> dict:
        img_type = {'type': 's3'}
        if filepath.startswith('https://drive.google'):
            img_type = {'type': 'gdrive', 'cred': _get_credentials(self.gdrive_ssm)}
        elif filepath.startswith('https://curate'):
            img_type = {'type': 'bendo'}
        return img_type

    def _set_processor(self, file):
        processor_info = self._get_processor_info(file.get('filePath'))
        src = processor_info.get('type')
        cred = processor_info.get('cred', None)
        self.processor = ProcessorFactory().get_processor(src, cred=cred)


def _get_credentials(ssm_key: str) -> dict:
    ssm = boto3.client('ssm')
    #parameter = ssm.get_parameter(Name=ssm_key, WithDecryption=True)
    #print(parameter['Parameter']['Value'])
    #return json.loads(parameter['Parameter']['Value'])
    #print(json.loads(parameter['Parameter']['Value']))
    return {'type': 'service_account', 'project_id': 'marble-nd', 'private_key_id': '13e993082b50b756e54b5a89eaf33ada80b73c42', 'private_key': '-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCzp6PVxujfcOpL\n7Atacl60zZ3+WU9GDNmiUe4GJU5A35GfRyy52oPcmyxbHn3iFGWgujFeTs7oHEr3\nfxXqNXtXqcUPRl4A6dC9b73MGSrvW7w9qC8JA3QKRAqLtEgyNXO1RgPySECnYGh5\nydQoIyePe6ZFQkt9KQtg6NBmy7nY+a8X4xwnOprbIs2dngTM0LrPyEx8D9i40zoE\nURCGjgi38V3EBI2y1/fEL7DmF/WOvXzTXMdDnyMRLXLwNGUe3zQ8wbW+rQ5y19Wi\nVMvfw1Mr2LJKiAxya4R1EWJu9Miv2OiYdrrxrkigTEMS3Xgo2ZpDq9BazAR6Vt9/\nxFoCgMhrAgMBAAECggEANz6w0ddF2xgE5G3km96Zou2rzQA3sWnYLuMU18z3AFn/\nlMQ1S72XWOpavHZm7XOqQL+g2MhRNe0lXHA3E/t4P1/UWjsgQxWje+11puKCYnKK\nM0eZlyL5twJvX8CDhvUK7M5n/kQbpZyu4+ydke4lhyjV22xkfEt31UgidcnmD4NM\nXA4YFaVEWdheTkA9PFQPdL7KzmjFU3rmbRzHrtMy0+aMtPkFo9VlhLUakdNFa+8j\n4KrmND+Z2aBkKBqtwiTX4NNGzRA4GMdWRJqpajf+6fhRMY2rN0u9AGuFnVC1Z40N\n3Jf5YezWsJMiPxD+FLfgGV0ktY8PIJyS4cXQUM1B6QKBgQDZ5Mu+El6k3HHLRwvj\ntNiVxZORu1ixx4PcB+wwtCoA3vfvfA5rxbFB7Z3olotJrv1it876e+iFHkK4SVOt\njLLl6Zy6dgIekTD4pr+mcuAiDCjT1aO8jrjFIE9gt9/AYfW8bUsBqyrqG1QoJqc2\nb+E2Mcd1JOOFGiBxFewSXLhQnQKBgQDTEt8EGRW1P0aygXlaQwczRP3SJhofiJ+J\nLOQLfIirha1YijkLECjkBjj5N67TfdR0TNS77y75mMzN06uIN5TjVUbNHhMso5sP\ny3cXUGPLKJ04GiHFcRtM8K2oBcjlMLqErHZT5T6tX4/ENe+jzgG3k0EmRNzDnpzZ\nD9ymBZFapwKBgDse30FFTrTAs4eKUWmJSjLpFu81vA0Qq3BqHeXhHHx8Ax3RtT/8\ntenDhVL0dfqaJlpAsUI5mI919Hh4POIcCPZk+oeFOXH9xyHQbLPG+5WBYxqHHxQs\nTWn/KEp/2ZAjhD+KEA312YEHxT/XrQsSNDM2Mn5QcgNNYXwNjK42xjPpAoGAJv1T\naORhWCuqGYtFKWE8UUIrSMh1BuIr5iD+twh4DocQ8EwIIX0IsKZdm9unVbXmqt0O\nZvDV0pFhM5woEW+C90NnYrhtfk9yc0Z4ZzwYUwzbjeN13Yz5KAtFaMY4x+1qZtuc\nt/6ex1PhsLLt42pIcuqmnDUYOqJwAsClV52rrf0CgYB/XyA/NYd7uyrmn/MeumsG\nulMwAA7XJ7HirKai9/8vfKdLfkC5S9Ig4X77Ynlt63eZafuNt5qaWMt0dazfMhY3\nq6lVlD8kQo83Wnw0dPb1SIrDzEuksYiYhuhxlon22aRJ7YSKu8TwnSAfuEf0+Hkg\nOhi528eDkN8qvMS91dlQlQ==\n-----END PRIVATE KEY-----\n', 'client_email': 'marble-data-processing@marble-nd.iam.gserviceaccount.com', 'client_id': '108537186876934448318', 'auth_uri': 'https://accounts.google.com/o/oauth2/auth', 'token_uri': 'https://oauth2.googleapis.com/token', 'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs', 'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/marble-data-processing%40marble-nd.iam.gserviceaccount.com'}


if __name__ == "__main__":
    try:
        event = json.loads(sys.argv[1])
        config = load_pipeline_config(event)
        runner = ImageRunner(config)
        runner.process_images()
    except Exception as e:
        print(e)
