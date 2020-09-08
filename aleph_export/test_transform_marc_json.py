# test_transform_marc_json.py
""" test transform_marc_json """
import _set_path  # noqa
import unittest
import json
import os
from pathlib import Path
from transform_marc_json import TransformMarcJson
from dependencies.pipelineutilities.pipeline_config import setup_pipeline_config  # noqa: E402


local_folder = os.path.dirname(os.path.realpath(__file__)) + "/"


class Test(unittest.TestCase):
    """ Class for test fixtures """
    def setUp(self):
        self.event = {"local": True}
        self.event['local-path'] = str(Path(__file__).parent.absolute()) + "/../example/"
        self.config = setup_pipeline_config(self.event)
        self.transform_marc_json_class = TransformMarcJson()
        filename = local_folder + 'test/sample_marc.json'
        with open(filename, 'r') as input_source:
            self.marc_record_as_json = json.load(input_source)

    def test_01_get_required_subfields(self):
        subfields_dict = {
            "subfields": [
                {"a": "Crocker, Richard L.,"},
                {"d": "1910-1963,"},
                {"e": "author,"},
                {"e": "performer."},
                {"0": "http://id.loc.gov/authorities/names/n85034882"},
                {"1": "http://viaf.org/viaf/28494769"}
            ]
        }
        subfields_needed_list = ["a", "b", "c", "e", "q"]
        sepcial_subfields_list = []
        actual_results = self.transform_marc_json_class._get_required_subfields(subfields_dict, subfields_needed_list, sepcial_subfields_list, " ")
        expected_results = "Crocker, Richard L., author, performer."
        self.assertTrue(actual_results == expected_results)
        sepcial_subfields_list = ["d"]
        actual_results = self.transform_marc_json_class._get_required_subfields(subfields_dict, subfields_needed_list, sepcial_subfields_list, " ")
        expected_results = "Crocker, Richard L., author, performer.^^^1910-1963,"
        self.assertTrue(actual_results == expected_results)

    def test_02_get_required_positions(self):
        input_string = "02253njm a2200457Ii 4500"
        positions_needed = [6]
        actual_results = self.transform_marc_json_class._get_required_positions(input_string, positions_needed)
        expected_results = "j"
        self.assertTrue(actual_results == expected_results)
        input_string = "190829s2009    cauccnn  di       n lat d"
        positions_needed = [35, 36, 37]
        actual_results = self.transform_marc_json_class._get_required_positions(input_string, positions_needed)
        expected_results = "lat"
        self.assertTrue(actual_results == expected_results)

    def test_03_default_to_appropriate_data_type(self):
        format = "array"
        actual_results = self.transform_marc_json_class._default_to_appropriate_data_type(format)
        self.assertTrue(isinstance(actual_results, list))
        format = "text"
        actual_results = self.transform_marc_json_class._default_to_appropriate_data_type(format)
        self.assertTrue(isinstance(actual_results, str))
        format = ""
        actual_results = self.transform_marc_json_class._default_to_appropriate_data_type(format)
        self.assertTrue(isinstance(actual_results, list))

    def test_04_verify_subfields_match(self):
        verify_subfields_match_dict = {"subfield": "x", "value": "MARBLE"}
        subfields_dict = {
            "subfields": [
                {"u": "https://rarebooks.library.nd.edu/digital/MARBLE-images/BOO_005063486/BOO_005194943/BOO_005194943_001.tif"},
                {"x": "MARBLE"}
            ]
        }
        actual_results = self.transform_marc_json_class._verify_subfields_match(verify_subfields_match_dict, subfields_dict)
        self.assertTrue(actual_results)
        verify_subfields_match_dict = {"subfield": "a", "value": "MARBLE"}
        actual_results = self.transform_marc_json_class._verify_subfields_match(verify_subfields_match_dict, subfields_dict)
        self.assertFalse(actual_results)

    def test_05_process_this_field(self):
        json_field_definition = {
            "label": "subjects",
            "fields": ["600", "689"],
            "selection": "range",
            "skipFields": ["655", "690"],
            "subfields": ["a", "b", "c", "d", "e", "f", "g", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"],
            "specialSubfields": ["0"],
            "extraProcessing": "format_subjects",
            "format": "array"
        }
        key = "650"
        value = {'subfields': [{'a': 'Gregorian chants.'}, {'2': 'fast'}, {'0': 'http://id.worldcat.org/fast/00947816'}], 'ind1': ' ', 'ind2': '7'}
        actual_results = self.transform_marc_json_class._process_this_field(json_field_definition, key, value)
        self.assertTrue(actual_results)
        key = "655"
        actual_results = self.transform_marc_json_class._process_this_field(json_field_definition, key, value)
        self.assertFalse(actual_results)
        json_field_definition = {
            "label": "workType",
            "fields": ["leader"],
            "positions": [6],
            "extraProcessing": "lookup_work_type",
            "format": "text"
        }
        key = "leader"
        value = "02219ccm a2200409Ki 4500"
        actual_results = self.transform_marc_json_class._process_this_field(json_field_definition, key, value)
        self.assertTrue(actual_results)

    def test_05a_process_this_field(self):
        """ Test restricting based on ind1 """
        json_field_definition = {
            "label": "uniqueIdentifier",
            "fields": ["852"],
            "subfields": ["h"],
            "specialSubfields": ["i"],
            "ind1": ["0"],
            "extraProcessing": "format_call_number",
            "format": "text"
        }
        key = "852"
        value = {'subfields': [{'h': 'M 1744 .B868'}, {'i': 'G4 1796'}], 'ind1': '0', 'ind2': '1'}
        actual_results = self.transform_marc_json_class._process_this_field(json_field_definition, key, value)
        self.assertTrue(actual_results)
        value = {'subfields': [{'h': 'M 1744 .B868'}, {'i': 'G4 1796'}], 'ind1': '4', 'ind2': '1'}
        actual_results = self.transform_marc_json_class._process_this_field(json_field_definition, key, value)
        self.assertFalse(actual_results)

    def test_06_get_value_from_marc_field(self):
        json_field_definition = {"label": "title", "fields": ["245"], "subfields": ["a", "b"], "format": "text"}
        actual_results = self.transform_marc_json_class._get_value_from_marc_field(json_field_definition, self.marc_record_as_json)
        expected_results = "New edition of a general Collection of the ancient Irish music : containing a variety of Irish Airs, never before published, and also the compositions of Conolan and Carolan, collected from the harpers, etc., in the different provinces of Ireland, and adapted for the pianoforte /"  # noqa
        self.assertTrue(actual_results == expected_results)
        json_field_definition = {"label": "collectionId", "fields": ["001"], "format": "text"}
        actual_results = self.transform_marc_json_class._get_value_from_marc_field(json_field_definition, self.marc_record_as_json)
        expected_results = "000297305"
        self.assertTrue(actual_results == expected_results)

    def test_07_get_json_node_value_from_marc(self):
        json_field_definition = {"label": "collectionId", "fields": ["001"], "format": "text"}
        actual_results = self.transform_marc_json_class._get_json_node_value_from_marc(json_field_definition, self.marc_record_as_json, {})
        expected_results = "000297305"
        self.assertTrue(actual_results == expected_results)
        json_field_definition = {"label": "publisher2", "otherNodes": "publisher", "format": "node"}
        actual_results = self.transform_marc_json_class._get_json_node_value_from_marc(json_field_definition, self.marc_record_as_json, {})
        expected_results = {'publisherName': 'published by I. Willis', 'publisherLocation': 'Dublin,'}
        self.assertTrue(actual_results == expected_results)

    def test_08_mutate_marc_record_as_json(self):
        mutated_marc_record_as_json = self.transform_marc_json_class._mutate_marc_record_as_json(self.marc_record_as_json)
        # with open(local_folder + 'test/sample_marc_mutated.json', 'w') as output_file:
        #     json.dump(mutated_marc_record_as_json, output_file, indent=2, default=str)
        with open(local_folder + 'test/sample_marc_mutated.json', 'r') as input_source:
            expected_json = json.load(input_source)
        self.assertTrue(mutated_marc_record_as_json == expected_json)

    def test_09_build_json_for_control_section(self):
        actual_results = self.transform_marc_json_class.build_json_for_control_section(self.marc_record_as_json, "publisher", {})
        expected_results = {'publisherName': 'published by I. Willis', 'publisherLocation': 'Dublin,'}
        self.assertTrue(actual_results == expected_results)

    def test_10_build_json_from_marc_json(self):
        actual_results = self.transform_marc_json_class.build_json_from_marc_json(self.marc_record_as_json)
        # with open(local_folder + 'test/sample_standard.json', 'w') as output_file:
        #     json.dump(actual_results, output_file, indent=2, default=str)
        with open(local_folder + 'test/sample_standard.json', 'r') as input_source:
            expected_json = json.load(input_source)
        file_created_date_from_sample = expected_json.get("fileCreatedDate", "")
        actual_results = self.fix_file_created_date(actual_results, file_created_date_from_sample)
        self.assertTrue(actual_results == expected_json)

    def fix_file_created_date(self, json_object, file_created_date):
        json_object["fileCreatedDate"] = file_created_date
        if "items" in json_object:
            for item in json_object["items"]:
                item = self.fix_file_created_date(item, file_created_date)
        return json_object


def suite():
    """ define test suite """
    return unittest.TestLoader().loadTestsFromTestCase(Test)


if __name__ == '__main__':
    suite()
    unittest.main()
