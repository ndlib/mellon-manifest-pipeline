import os
import json
from do_extra_processing import do_extra_processing
from pipelineutilities.validate_json import schema_api_version, validate_standard_json
from get_value_from_external_process import get_value_from_external_process, get_seed_nodes_json


class TransformMarcJson():
    """ This performs all Marc-related processing """
    def __init__(self):
        """ Save values required for all calls """
        local_folder = os.path.dirname(os.path.realpath(__file__))
        self.json_control = read_marc_to_json_translation_control_file(local_folder + "/marc_to_json_translation_control_file.json")  # noqa: E501
        self.schema_api_version = schema_api_version()

    def build_json_from_marc_json(self, marc_record_as_json: dict) -> dict:
        """ Build our own json object representing marc information we're interested in """
        marc_record_as_json = self._mutate_marc_record_as_json(marc_record_as_json)
        standard_json = self.build_json_for_control_section(marc_record_as_json, 'root', {})
        if not validate_standard_json(standard_json):
            standard_json = {}
        return standard_json

    def build_json_for_control_section(self, marc_record_as_json: dict, section_name: str, seeded_json: dict) -> dict:
        # json_record = {}
        json_record = seeded_json.copy()
        for json_field_definition in self.json_control[section_name]['FieldsToExtract']:
            if 'label' in json_field_definition:
                json_record[json_field_definition['label']] = self._get_json_node_value_from_marc(json_field_definition, marc_record_as_json, json_record)  # noqa: E501
        return json_record

    def _mutate_marc_record_as_json(self, marc_record_as_json: dict) -> dict:
        """ For expediency, I will add the leader key to the fields array to capture workType.
        Then, everything I need will be under the "fields" array. """
        if "leader" in marc_record_as_json and "fields" in marc_record_as_json:
            node_to_add = {}
            node_to_add["leader"] = marc_record_as_json["leader"]
            marc_record_as_json["fields"].append(node_to_add)
        return marc_record_as_json

    def _get_json_node_value_from_marc(self, json_field_definition: dict, marc_record_as_json: dict, json_record: dict) -> str:
        """ Return an individual json node value from the json representation of the marc record. """
        results = ""
        if 'constant' in json_field_definition:
            results = json_field_definition.get("constant", "")
        elif 'externalProcess' in json_field_definition:
            results = get_value_from_external_process(json_record, json_field_definition, self.schema_api_version)
        elif 'otherNodes' in json_field_definition:
            seed_json = {}
            if 'seedNodes' in json_field_definition:
                seed_nodes_control = json_field_definition.get('seedNodes', '')
                seed_json = get_seed_nodes_json(json_record, seed_nodes_control)
            preliminary_results = self.build_json_for_control_section(marc_record_as_json, json_field_definition.get('otherNodes', ''), seed_json)
            if json_field_definition.get("format", "") == "array":
                results = []
                results.append(preliminary_results)
            else:
                results = preliminary_results
        else:
            results = self._get_value_from_marc_field(json_field_definition, marc_record_as_json)
        return results

    def _get_value_from_marc_field(self, json_field_definition: dict, marc_record_as_json: dict) -> dict:
        """ More detailed logic to extract value from json representation of marc record,
            as defined by marc_to_json_translation_control_file.json """
        subfields_needed = json_field_definition.get("subfields", "")
        subfield_separator = json_field_definition.get("subfieldSeparator", " ")
        positions = json_field_definition.get("positions", "")
        format = json_field_definition.get("format", "")
        extra_processing = json_field_definition.get("extraProcessing", "")
        special_subfields = json_field_definition.get("specialSubfields", "")
        node = self._default_to_appropriate_data_type(format)
        for field in marc_record_as_json['fields']:
            for key, value in field.items():
                if self._process_this_field(json_field_definition, key, value):
                    if 'subfields' in value:
                        value_found = self._get_required_subfields(value, subfields_needed, special_subfields, subfield_separator)
                    elif positions != "":
                        value_found = self._get_required_positions(value, positions)
                    else:
                        value_found = value
                    if value_found is not None and value_found != "":
                        if format == "text":
                            node = value_found  # redefine node as string here
                            break  # get out if we're only looking for a single value
                        else:
                            node.append(value_found)
            else:
                continue  # only executed if inner loop did NOT break
            break  # only executed if inner loop DID break
        if extra_processing != "":
            node = do_extra_processing(node, extra_processing)
        return node

    def _process_this_field(self, json_field_definition: dict, key: str, value: str) -> str:
        """ This returns a boolean indicating whether or not this field should be processed """
        results = False
        fields = json_field_definition.get("fields", "")
        skip_fields = json_field_definition.get("skipFields", "")
        selection = json_field_definition.get("selection", "")
        ind1 = json_field_definition.get("ind1", "")
        if selection == 'range':
            start_of_range = fields[0]
            end_of_range = fields[len(fields) - 1]
            if key >= start_of_range and key <= end_of_range and key not in skip_fields:
                results = True
        elif key in fields and key not in skip_fields:
            results = True
        if results and 'verifySubfieldsMatch' in json_field_definition:
            results = self._verify_subfields_match(json_field_definition['verifySubfieldsMatch'], value)
        if results and ind1:
            if "ind1" in value:
                results = (value["ind1"] in ind1)
        return results

    def _verify_subfields_match(self, verify_subfields_match: dict, subfields: dict) -> bool:
        """ For Marc field 956, we only want to harvest those records with a subfield for MARBLE.
            This returns a boolean value after applying this logic.
            Note this has a loop, which seem rediculous, but we really do need a loop in case an image
            will be used by multiple systems, say MARBLE and something else.  We need to loop through all
            possibe cases, in case there are multiples. """
        results = False
        if 'subfields' in subfields:
            for subfield in subfields['subfields']:
                for key, value in subfield.items():
                    if key == verify_subfields_match['subfield'] and value == verify_subfields_match['value']:
                        results = True
        return results

    def _default_to_appropriate_data_type(self, format: str) -> str:
        """ Create a node with the appropriate data type defined in the control file. """
        node = []
        if format == "text":
            node = ""
        return node

    def _get_required_positions(self, value: str, positions_needed: list) -> str:
        """ Extract values from specific positions within a string """
        results = ""
        for position in positions_needed:
            if len(value) >= position:
                results += value[position]
        return results

    def _get_required_subfields(self, subfields: dict, subfields_needed: list, special_subfields: list, subfield_separator: str) -> dict:
        """ Append values from subfields we're interested in """
        results = ""
        for subfield in subfields['subfields']:
            for key, value in subfield.items():
                if key in subfields_needed:
                    if results == "":
                        results = value
                    else:
                        results += subfield_separator + value
        if special_subfields:  # separate special subfields, at the end of the string
            subfield_results = self._get_required_subfields(subfields, special_subfields, [], subfield_separator)
            if subfield_results:
                results += "^^^" + subfield_results
        return results


def read_marc_to_json_translation_control_file(filename: str):
    """ Read json file which defines marc_json to json translation """
    try:
        with open(filename, 'r') as input_source:
            data = json.load(input_source)
        input_source.close()
    except IOError:
        print('Cannot open ' + filename)
        raise
    return data
