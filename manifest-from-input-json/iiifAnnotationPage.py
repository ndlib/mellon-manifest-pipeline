from iiifItem import iiifItem
from iiifAnnotation import iiifAnnotation


class iiifAnnotationPage(iiifItem):
    def __init__(self, id, config):
        iiifItem.__init__(self, id, 'AnnotationPage')
        self.config = config

    def page(self):
        return {
            'id': 'AnnotationUrl',
            'type': self.type,
            'items': [
                iiifAnnotation(self.id, self.config).annotation()
            ]
        }
