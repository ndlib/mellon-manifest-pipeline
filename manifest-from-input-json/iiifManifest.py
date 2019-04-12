from iiifImage import iiifImage
from iiifSequence import iiifSequence


class iiifManifest():
    def __init__(self, id, event_config, manifest_data):
        self.id = id
        self.manifest_id = event_config['manifest-server-base-url'] + '/' + self.id + '/manifest'
        self.config = event_config
        self.manifest_data = manifest_data

    def manifest(self):
        manifest = {
            '@context': 'http://iiif.io/api/presentation/2/context.json',
            '@type': 'sc:Manifest',
            '@id': self.manifest_id,
            'label': self.manifest_data['label'],
            'metadata': self.manifest_data['metadata'],
            'description': self.manifest_data['description'],
            'license': self.manifest_data['license'],
            'attribution': self.manifest_data['attribution'],
            'viewingDirection': self.manifest_data['viewingDirection'],
            'thumbnail': self.thumbnail(),
            'sequences': self.sequences()
        }
        # add optional data
        if 'homepage' in self.manifest_data:
            manifest['homepage'] = self.manifest_data['homepage']
        if 'seeAlso' in self.manifest_data:
            manifest['seeAlso'] = self.manifest_data['seeAlso']
        return manifest

    def sequences(self):
        ret = []
        if 'sequences' in self.manifest_data:
            for sequence_data in self.manifest_data['sequences']:
                ret.append(iiifSequence(self.id, self.config, sequence_data).sequence())
        return ret

    def thumbnail(self):
        default_page = self.manifest_data['sequences'][0]['pages'][0]
        for page in self.manifest_data['sequences'][0]['pages']:
            if page['file'] == self.config['default-img']:
                default_page = page.copy()
                default_page['file'] = 'default'
        return iiifImage(self.id, default_page['file'], default_page['label'], self.config).thumbnail()
