import boto3
import os
import json
from botocore.errorfactory import ClientError
from dependencies.pipelineutilities.s3_helpers \
    import get_matching_s3_objects, s3_copy_data, read_s3_file_content, delete_file


class FinalizeStep():
    def __init__(self, id, eventConfig):
        self.id = id
        self.config = eventConfig
        self.error = []

    def run(self):
        if self.success():
            self.image_cleanup()
            self.move_pyramids()
            self.move_metadata()
        self.notify()

    def success(self):
        return True
        if self.error:
            return False
        return True

    def move_pyramids(self):
        src_bucket = self.config['process-bucket']
        dest_bucket = self.config['image-server-bucket']
        src_path = f"{self.config['process-bucket-read-basepath']}/{self.id}/images/"
        img_data_path = f"{self.config['process-bucket-read-basepath']}/{self.id}/image_data.json"

        try:
            img_data = json.loads(read_s3_file_content(src_bucket, img_data_path))
        except boto3.resource('s3').meta.client.exceptions.NoSuchKey:
            img_data = {}
        except ValueError as ve:  # includes simplejson.decoder.JSONDecodeError
            print(f"Failed move_pyramids for - {img_data_path}")
            print(f"ValueError Exception - {ve}")
            img_data = {}

        all_objects = get_matching_s3_objects(src_bucket, src_path)
        for obj in all_objects:
            # only copy those files that have changed
            file = os.path.basename(obj['Key'])
            filename = file.rsplit('.', maxsplit=1)[0]
            reason = img_data.get(filename, {}).get('reason', '')
            if reason.startswith('no changes'):
                continue
            dest_key = f"{self.id}/{file}"
            s3_copy_data(dest_bucket, dest_key, src_bucket, obj['Key'])
        return

    def image_cleanup(self):
        src_bucket = self.config['process-bucket']
        dest_bucket = self.config['image-server-bucket']
        src_path = f"{self.config['process-bucket-read-basepath']}/{self.id}/images"
        img_data = f"{self.config['process-bucket-read-basepath']}/{self.id}/image_data.json"
        latest_images = get_matching_s3_objects(src_bucket, src_path)
        public_images = get_matching_s3_objects(dest_bucket, self.id)
        latest = set()  # images in the process bucket
        public = set()  # images in the image server bucket
        manifest = set()  # images listed in processbucket/{id}/image_data.json

        for image in public_images:
            public.add(os.path.basename(image['Key']))
        for image in latest_images:
            latest.add(os.path.basename(image['Key']))

        try:
            manifest_data = json.loads(read_s3_file_content(src_bucket, img_data))
            for image in manifest_data:
                manifest.add(f"{image}.tif")
        except boto3.resource('s3').meta.client.exceptions.NoSuchKey:
            pass
        except ValueError as ve:  # includes simplejson.decoder.JSONDecodeError
            print(f"Failed cleanup process for - {img_data}")
            print(f"ValueError Exception - {ve}")
        except Exception as e:
            print(f"Failed cleanup process for - {img_data}")
            print(e)

        # delete pyramids in process bucket but not in image_data.json
        self._delete_obsolete_pyramids(src_bucket, src_path, latest.difference(manifest))

        # delete pyramids in image server bucket but not in process bucket
        self._delete_obsolete_pyramids(dest_bucket, self.id, public.difference(latest))

    def _delete_obsolete_pyramids(self, bucket, path, images, **kwargs) -> set:
        deleted_images = set()
        return deleted_images  # Added 8/19/20 to make sure we don't accidentally remove images we shouldn't - per Jon
        for image in images:
            print(f"Removing - {path}/{image} from {bucket}")
            if kwargs.get('local', False):
                response = {'DeleteMarker': True}
            else:
                try:
                    response = delete_file(bucket, f"{path}/{image}")
                except Exception as e:
                    print(e)
                    response = {'DeleteMarker': False}
            if response.get('DeleteMarker'):
                deleted_images.add(image)
        return deleted_images

    def move_metadata(self):
        src_bucket = self.config['process-bucket']
        dest_bucket = self.config['manifest-server-bucket']
        src_path = f"{self.config['process-bucket-read-basepath']}/{self.id}/metadata/"

        all_objects = get_matching_s3_objects(src_bucket, src_path)
        for obj in all_objects:
            dest_key = obj['Key'].replace('metadata/', '').replace('process/', '')
            s3_copy_data(dest_bucket, dest_key, src_bucket, obj['Key'])
        return

    def notify(self):
        return

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
