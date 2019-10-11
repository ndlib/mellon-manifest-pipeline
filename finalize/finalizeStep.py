import json
import os
import boto3
from botocore.errorfactory import ClientError
from pathlib import Path


class finalizeStep():
    # class constructor
    def __init__(self, id, eventConfig):
        self.id = id
        self.config = eventConfig
        self.error = []

    def run(self):
        if self.success():
            self.movePyramids()
            self.moveManifest()
            self.moveSchema()
            self.moveMets()
            # self.saveLastRun()
        self.notify()

    def success(self):
        if self.error:  # or len(self.manifest_metadata["errors"]) > 0:
            return False

        return True

    # clones an established default image to an image named default.jpg
    def copyDefaultImg(self):
        print("make default image")
        bucket = self.config['process-bucket']
        remote_file = self.config['process-bucket-write-basepath'] + "/" + self.id + "/images/" + Path(self.manifest_metadata['thumbnail']).stem + ".tif"
        default_image = self.config['process-bucket-write-basepath'] + "/" + self.id + "/images/default.tif"
        copy_source = {
            'Bucket': bucket,
            'Key': remote_file
        }
        boto3.resource('s3').Bucket(bucket).copy(copy_source, default_image)

    def movePyramids(self):
        print("movePyramids")

        s3 = boto3.resource('s3')

        from_bucket = s3.Bucket(self.config["process-bucket"])
        to_bucket = s3.Bucket(self.config["image-server-bucket"])

        from_path = self.config["process-bucket-write-basepath"] + "/" + self.id + "/images/"
        all_objects = from_bucket.object_versions.filter(Prefix=from_path, Delimiter="/")

        for o in all_objects:
            copy_source = {
                'Bucket': self.config["process-bucket"],
                'Key': o.object_key
            }
            other_key = self.config["image-server-bucket-basepath"] + self.id + "/" + os.path.basename(o.object_key)
            to_bucket.copy(copy_source, other_key)
        return

    def moveManifest(self):
        s3 = boto3.resource('s3')
        copy_source = {
            'Bucket': self.config["process-bucket"],
            'Key': self.config["process-bucket-write-basepath"] + "/" + self.id + "/manifest/index.json"
        }

        bucket = s3.Bucket(self.config["manifest-server-bucket"])
        print(copy_source)

        other_key = self.test_basepath(self.config["manifest-server-bucket-basepath"]) \
            + self.id + "/manifest/index.json"
        bucket.copy(copy_source, other_key, ExtraArgs={'ACL': 'public-read'})

        return

    def moveSchema(self):
        s3 = boto3.resource('s3')
        copy_source = {
            'Bucket': self.config["process-bucket"],
            'Key': self.config["process-bucket-write-basepath"] + "/" + self.id + "/" + self.config['schema-file']
        }

        bucket = s3.Bucket(self.config["manifest-server-bucket"])
        print(copy_source)

        other_key = self.test_basepath(self.config["manifest-server-bucket-basepath"]) \
            + self.id + "/index.json"
        bucket.copy(copy_source, other_key, ExtraArgs={'ACL': 'public-read'})

        return

    def moveMets(self):
        if self.config['metadata-source-type'] == 'mets':
            s3 = boto3.resource('s3')
            copy_source = {
                'Bucket': self.config["process-bucket"],
                'Key': self.config["process-bucket-write-basepath"] + "/" + self.id + "/mets.xml"
            }

            bucket = s3.Bucket(self.config["manifest-server-bucket"])
            print(copy_source)

            other_key = self.test_basepath(self.config["manifest-server-bucket-basepath"]) \
                + self.id + "/mets.xml"
            bucket.copy(copy_source, other_key, ExtraArgs={'ACL': 'public-read'})

        return

    def saveLastRun(self):
        print("Save Last Run")
        s3 = boto3.resource('s3')

        from_path = self.config["process-bucket-read-basepath"] + "/" + self.id + "/"
        # all the items in the process directory for the id
        try:
            objects = self._list_s3_obj_by_dir(from_path, self.config["process-bucket"])

            for s3obj in objects:
                copy_src = {'Bucket': self.config["process-bucket"], 'Key': s3obj}
                dest_key = self.config["process-bucket-write-basepath"] + "/" \
                    + self.id + "/lastSuccessfullRun/" + s3obj[len(from_path):]
                s3.Object(self.config["process-bucket"], dest_key).copy_from(CopySource=copy_src)
        except Exception as e:
            print(e)

    def _list_s3_obj_by_dir(self, s3dir, bucket):
        s3 = boto3.client('s3')
        params = {
            'Bucket': bucket,
            'Prefix': s3dir,
            'StartAfter': s3dir,
        }
        attempt = 0
        keys = []
        while ('ContinuationToken' in params) or (attempt == 0):
            attempt += 1
            objects = s3.list_objects_v2(**params)
            for content in objects['Contents']:
                # skip 'folders'
                if content['Key'].endswith('/'):
                    continue
                keys.append(content['Key'])
            # grab more objects to process if necessary(max 1,000/request)
            if objects['IsTruncated']:
                params['ContinuationToken'] = objects['NextContinuationToken']
            else:
                params.pop('ContinuationToken', None)
        return keys

    def notify(self):
        if self.success():
            if self.config.get('notify-on-finish', False):
                recipients = self.config['notify-on-finished'].split(",")
            else:
                recipients = ['jhartzle@nd.edu']

            subject = self.id + " Manifest Pipeline Complete"
            body_text = "The manifest pipeline has completed processing " + self.id
            body_html = """<html>
            <head></head>
            <body>
            <h1>""" + self.id + """ manifest pipeline has completed</h1>
            <p>CSVs and images have been processed through the pipeline.</p>
            <ul>
                <li><a href=\"""" + self._event_manifest_url() + """\">Manifest</a></li>
                <li><a href=\"""" + self._event_imageviewer_url() + """\">Image Viewer</a></li>
                <li><a href=\"""" + self._event_imageviewer_url(True) + """\">Image Viewer - Large</a></li>
            </ul>
            </body>
            </html>"""
        else:
            recipients = []
            if self.config.get('notify-on-finished', False):
                recipients = self.config.get('notify-on-finished').split(",")
            recipients.append(self.config['troubleshoot-email-addr'])
            subject = "Error processing " + self.id
            if self.error:
                reportable_errs = "<li>" + str(self.error) + "</li>"
            else:
                for err in self.config.get("errors", []):
                    reportable_errs += "<li>" + err + "</li>"
            body_html = """<html>
            <head></head>
            <body>
            <h1>""" + self.id + """ failed with errors!</h1>
            <p>The pipeline failed for the following reasons:</p>
            <ul>""" + reportable_errs + """</ul>
            </body>
            </html>"""
            body_text = "The following errors were encountered processing: " \
                + reportable_errs

        self._send_notification(recipients, subject, body_html, body_text)

        return

    def _send_notification(self, recipients, subject, body_html, body_text):
        SENDER = self.config['noreply-email-addr']
        AWS_REGION = "us-east-1"
        CHARSET = "UTF-8"
        client = boto3.client('ses', region_name=AWS_REGION)
        try:
            # Provide the contents of the email.
            response = client.send_email(
                Destination={
                    'ToAddresses': recipients,
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': body_html,
                        },
                        'Text': {
                            'Charset': CHARSET,
                            'Data': body_text,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': subject,
                    },
                },
                Source=SENDER
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])
        return

    def _event_manifest_url(self):
        return self.config['manifest-server-base-url'] \
            + "/" + self.id + '/manifest/index.json'

    def _event_imageviewer_url(self, universalviewer=False):
        url = 'https://viewer-iiif.library.nd.edu/'
        if universalviewer:
            url += 'universalviewer/index.html#'
        url += '?manifest=' + self._event_manifest_url()
        return url

    def test_basepath(self, basepath):
        if (basepath):
            return basepath + "/"

        return ""
