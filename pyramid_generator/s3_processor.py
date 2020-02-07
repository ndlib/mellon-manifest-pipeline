from image_processor import ImageProcessor


class S3ImageProcessor(ImageProcessor):
    def __init__(self) -> None:
        super().__init__()

    def process(self) -> dict:
        if self._previously_processed():
            file_info = self.prior_results.get(self.id).get(self.filename)
            height = file_info.get('height', 2000)
            width = file_info.get('width', 2000)
            md5sum = file_info.get('md5sum', '')
            self._log_result('status', 'processed')
            self._log_result('height', height)
            self._log_result('width', width)
            self._log_result('md5sum', md5sum)
            self._log_result('reason', 'no changes to image since last run')
        else:
            img_bucket, key = self.source_image.split('/', 2)[-1].split('/', 1)
            s3_file = f"{self.img_write_base}/{self.id}/images/{self.tif_file}"
            self.S3_RESOURCE.Bucket(img_bucket).download_file(key, self.local_file)
            self._generate_pytiff(self.local_file, self.tif_file)
            self.S3_RESOURCE.Bucket(self.bucket).upload_file(self.tif_file, s3_file)
            self._cleanup()
            self._log_result('status', 'processed')
        return self.image_result
