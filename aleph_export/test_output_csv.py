# test_output_csv.py
""" test output_csv """

import unittest
from output_csv import OutputCsv


class Test(unittest.TestCase):
    """ Class for test fixtures """

    def test_output_csv(self):
        """ Write header and a record, and verify what was written. """
        csv_field_names = ["a", "b", "c"]
        json_record = {"a": 1, "b": 2, "c": 3, "d": 4}  # verifying extra fields do not show up in output
        output_csv_class = OutputCsv(csv_field_names)
        output_csv_class.write_csv_row(json_record)
        csv_string = output_csv_class.return_csv_value()
        expected_output = '"a","b","c"\r\n"1","2","3"\r\n'
        self.assertTrue(csv_string == expected_output)


def suite():
    """ define test suite """
    return unittest.TestLoader().loadTestsFromTestCase(Test)


if __name__ == '__main__':
    suite()
    unittest.main()