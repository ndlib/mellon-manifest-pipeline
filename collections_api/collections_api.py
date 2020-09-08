import time
import os
import re
import json  # noqa: F401
from s3_helpers import read_s3_json, get_matching_s3_objects, write_s3_json


class CollectionsApi():
    def __init__(self, config):
        self.config = config
        self.start_time = time.time()
        self.local_folder = os.path.dirname(os.path.realpath(__file__)) + "/"

    def save_collection_details(self, source_list: list):
        if not source_list:
            source_list = ['aleph', 'archivesspace', 'curate', 'embark']
        all_collections_details = []
        for source in source_list:
            collection_list = self._get_collection_list(source)
            if len(collection_list):
                collection_details = self._get_collection_details(collection_list)
                if len(collection_details):
                    all_collections_details.append(collection_details)
                    s3_key = os.path.join('collections', source, 'index.json')
                    # print("About to write collection_details to ", self.config['manifest-server-bucket'], s3_key)
                    write_s3_json(self.config['manifest-server-bucket'], s3_key, collection_details)
        if all_collections_details:
            s3_key = 'collections/all/index.json'
            write_s3_json(self.config['manifest-server-bucket'], s3_key, collection_details)
        #  These need to be saved directly into the manifest bucket so we can serve from here:
        # https://presentation-iiif.library.nd.edu/collections
        return

    def _get_collection_list(self, source: str = "") -> list:
        """ Get a listing of collections by source.  If no source is specified, return all."""
        collection_list = []
        patterns = {
            "aleph": r"(^[0-9]{9}/standard/index\.json$)",
            "archivesspace": r"(^[A-Z]*[0-9]*_EAD/standard/index\.json$)",
            "curate": r"(^[a-z0-9]{11}/standard/index\.json$)",
            "embark": r"(^[A-Z]*[0-9]{4}.[.0-9]*[.a-z]*/standard/index\.json$)",
        }
        complete_list = self._call_get_matching_s3_objects(self.config["manifest-server-bucket"], "", "/standard/index.json")
        if source:
            regex = patterns.get(source, "^source was specified but no pattern found so do not return results")
        else:
            regex = ".*"  # if no source was indicated, return everything
        for file_info in complete_list:
            key = file_info.get('Key', '')
            if re.search(regex, key):
                collection_list.append(re.sub('^', '', re.sub('/standard/index.json$', '', key)))
        collection_list.sort()
        return collection_list

    def _call_get_matching_s3_objects(self, bucket: str, prefix: str = "", suffix: str = "") -> dict:
        """ This only exists so I can mock it """
        matching_objects = get_matching_s3_objects(bucket, prefix, suffix)
        # I'll keep this here in case I need to re-save results of get_matching_s3_objects
        # filename = os.path.join(self.local_folder, 'test/matching_s3_objects.json')
        # local_complete_list = []
        # for file_info in matching_objects:
        #     local_complete_list.append(file_info)
        # with open(filename, 'w') as f:
        #     json.dump(local_complete_list, f, indent=2, default=str)
        return matching_objects

    def _get_collection_details(self, collection_list: list) -> dict:
        collection_details = []
        for id in collection_list:
            collection_details.append(self._get_item_details(id))
        return collection_details

    def _get_item_details(self, id: str) -> dict:
        details = {}
        item_json = self._get_id(id)
        base_url = "https://presentation-iiif.library.nd.edu/collections"
        if item_json:
            details['id'] = item_json.get('id', '')
            details['url'] = os.path.join(base_url, id)
            details['title'] = item_json.get('title', '')
            if item_json.get('linkToSource', ''):
                details['sourceSystemUri'] = item_json['linkToSource']
        return details

    def _get_id(self, id: str) -> dict:
        """ Return content for an individual id."""
        item_json = {}
        key = os.path.join(self.config["process-bucket-data-basepath"], id + '.json')
        if id:
            item_json = read_s3_json(self.config['process-bucket'], key)
        return item_json
