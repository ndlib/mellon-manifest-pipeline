import xml.etree.ElementTree as ET
from io import StringIO
from pathlib import Path
import os


class MetsToSchema():
    def __init__(self, config, descriptive_metadata, structural_metadata, image_data):
        self.descriptive_xml = self.xml_to_dict(descriptive_metadata)
        self.structural_xml = self.xml_to_dict(structural_metadata)
        self.config = config
        self.image_data = image_data

        self.descriptive_namespaces = dict([
            node for _, node in ET.iterparse(
                StringIO(descriptive_metadata), events=['start-ns']
            )
        ])

        self.structural_namespaces = dict([
            node for _, node in ET.iterparse(
                StringIO(structural_metadata), events=['start-ns']
            )
        ])

        self.id = self.descriptive_xml.find('.//dcterms:identifier', self.descriptive_namespaces).text
        self.base_url = config['manifest-server-base-url'] + "/" + self.id
        self.default_image = {}
        self.has_part_items = self.has_part_items()
        self.main_item = self.main_item()
        self.errors = []

    def get_json(self):
        graph = [self.main_item] + self.has_part_items
        return {
            "@context": "http://schema.org",
            "@graph": graph
        }

    def main_item(self):
        fieldmap = self.mappings()
        main = {"@id": self.base_url, "@type": "CreativeWork"}
        for schema_key, xml_xpath in fieldmap.items():
            xml_xpath = ".//" + xml_xpath
            xml_value = self.descriptive_xml.find(xml_xpath, self.descriptive_namespaces)
            if xml_value is not None and xml_value.text is not None:
                main[schema_key] = xml_value.text

        main['thumbnail'] = self.default_image
        main["hasPart"] = []
        for hasPartItem in self.has_part_items:
            main["hasPart"].append(hasPartItem["@id"])

        return main

    def xml_to_dict(self, xml):
        return ET.fromstring(xml)

    def has_part_items(self):
        xml_xpath = './/mets:structMap/mets:div/mets:div'
        xml_value = self.structural_xml.findall(xml_xpath, self.structural_namespaces)

        ret = []
        for index, item in enumerate(xml_value):
            filename = item.find('.//mets:fptr', self.structural_namespaces).attrib['FILEID'].replace('ID_', '')
            filename = self.filename_with_tif_extension(filename)

            position = item.attrib['ORDER']
            name = item.attrib['LABEL']
            file = Path(filename).stem
            schemaImage = {
                "@id": self.config['image-server-base-url'] + "/" + self.id + "%2F" + filename,
                "@type": "ImageObject",
                "name": name,
                "caption": "",
                "height": str(self.image_data[file]['height']),
                "width": str(self.image_data[file]['width']),
                "contentUrl": self.config['image-server-base-url'] + "/" + self.id + "%2F" + filename,
                "position": str(position),
                "isPartOf": self.base_url,
                "identifier": self.id + "%2F" + filename,
            }
            ret.append(schemaImage)

        if (not self.default_image):
            self.default_image = ret[0]['@id']

        return ret

    def mappings(self):
        return {
          "identifier": "dcterms:identifier",
          "name": "dcterms:title",
          "creator": "dcterms:creator",
          "dateCreated": "dcterms:created",
          "materialExtent": "dcterms:extent",
          "copyrightHolder": "dcterms:rights",
          "license": "dcterms:license",
          "conditionOfAccess": "dcterms:accessRights",
          "sponsor": "dcterms:provenance",
          "provider": "dcterms:publisher",
          "subject": "dcterms:subject",
          "description": "dcterms:description",
          # "material": "vracore:display",
          # "dateModified": "vracore:latestDate"
        }

    def filename_with_tif_extension(self, file):
        return os.path.splitext(file)[0] + '.tif'

#           "temporalCoverage": "dcterms:created",
#         <dcterms:type>artMedium</dcterms:type>
#  <dcterms:format>artMedium</dcterms:format>
