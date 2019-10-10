from iiifImage import iiifImage
from iiifCanvas import iiifCanvas
from iiifItem import iiifItem


class iiifManifest(iiifItem):
    def __init__(self, config, data):
        self.id = config['id']
        config['event_id'] = config['id']
        self.config = config
        self._process_graph(data)
        iiifItem.__init__(self, self.id, self._schema_to_manifest_type())

    def manifest(self):
        ret = {
            'type': self.type,
            'id': self._manifest_id(),
            'label': self._lang_wrapper(self.creativework_data['name']),
            'thumbnail': self.thumbnail(),
            'items': self._items(),
            'viewingDirection': 'left-to-right',
            'seeAlso': [{
                "id": self.creativework_data['@id'],
                "type": "Dataset",
                "format": "application/ld+json",
                "profile": "https://schema.org/"
            }],
            'metadata': []
        }
        if self.creativework_data.get('conditionOfAccess', False):
            ret['requiredStatement'] = self._convert_label_value('Condition Of Access', self.creativework_data['conditionOfAccess'])

        if self.creativework_data.get('license', False):
            ret['rights'] = self.creativework_data['license']

        if self.creativework_data.get('description', False):
            ret['summary'] = self._lang_wrapper(self.creativework_data['description'])

        if self.config['metadata-source-type'] == 'mets':
            ret['seeAlso'].append({
                "id": self.config['manifest-server-base-url'] + '/' + self.id + '/mets.xml',
                "type": "Dataset",
                "format": "application/xml",
                "profile": "http://www.loc.gov/METS/"
            })

        for key, label in self._schema_to_metadata_mappings().items():
            if self.creativework_data.get(key, False):
                ret['metadata'].append(self._convert_label_value(label, self.creativework_data[key]))

        return ret

    def thumbnail(self):
        if 'thumbnail' in self.creativework_data:
            item = self._find_image_in_items(self.creativework_data['thumbnail'])
            if item:
                return [iiifImage(item['identifier'], self.config).thumbnail()]

        return []

    def _items(self):
        ret = []
        for item_data in self.images:
            if (item_data['@type'].lower() == 'imageobject'):
                # file = Path(item_data['contentUrl']).stem
                # item_data['width'] = self.image_data[file]['width']
                # item_data['height'] = self.image_data[file]['height']

                ret.append(iiifCanvas(item_data, self.config).canvas())
            elif (item_data['@type'] == 'Manifest'):
                tempConfig = self.config
                tempConfig['id'] = item_data['id']
                ret.append(iiifManifest(self.config, item_data, self.image_data).manifest())
            elif (item_data['@type'] == 'Collection'):
                ret.append(iiifManifest(self.config, item_data, self.image_data).manifest())

        return ret

        return []

    def _schema_to_manifest_type(self):
        if self.creativework_data['@type'].lower() == 'creativework':
            return 'Manifest'
        elif self.creativework_data['@type'] == 'creativeworkseries':
            return 'Collection'

        raise "invalid schema processor type"

    def _process_graph(self, data):
        self.images = []
        for item in data['@graph']:
            if item['@type'].lower() == 'creativework':
                self.creativework_data = item
            elif item['@type'].lower() == 'imageobject':
                self.images.append(item)

    def _manifest_id(self):
        if self.type == 'Manifest':
            return self.config['manifest-server-base-url'] + '/' + self.id + '/manifest'
        else:
            return self.config['manifest-server-base-url'] + '/collection/' + self.id

    def _find_image_in_items(self, image):
        for item in self.images:
            if (item['@id'] == image):
                return item

        return False

    def _convert_label_value(self, label, value):
        if (label and value):
            return {
                'label': self._lang_wrapper(label),
                'value': self._lang_wrapper(value)
            }
        return None

    def _schema_to_metadata_mappings(self):
        return {
          "creator": "Creator",
          "dateCreated": "Date",
          "materialExtent": "Material Extent",
          "copyrightHolder": "Copyright Holder",
          "conditionOfAccess": "Condition Of Access",
          "sponsor": "Provienance",
          "subject": "Subject",
        }