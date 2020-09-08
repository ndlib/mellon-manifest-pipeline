import _set_test_path  # noqa
import unittest
from datetime import datetime, timedelta
from finalize.finalizeStep import FinalizeStep
from finalize.handler import setup_config_for_restarting_step, break_to_restart_step, finalize_is_complete

test_id = "sample"

test_config = {
    "process-bucket": "mybucket",
    "process-bucket-read-basepath": f"process/{test_id}/images",
    "image-server-bucket": "anotherbucket"
}


class TestFinalize(unittest.TestCase):

    def test_image_cleanup(self):
        step = FinalizeStep(test_id, test_config)
        bucket = test_config["process-bucket"]
        path = test_config["process-bucket-read-basepath"]
        images = set(["img1.tif", "img2.tif", "img3.tif", "img4.tif"])
        deleted_images = step._delete_obsolete_pyramids(bucket, path, images, local='y')  # noqa: F841
        # self.assertEqual(images, deleted_images)  # temporarily removed 8/19/20

    def test_setup_config_for_restarting_step(self):
        test = {"seconds-to-allow-for-processing": 100}
        setup_config_for_restarting_step(test)
        self.assertEqual(test['finalize_completed_ids'], [])
        self.assertEqual(test['finalize_run_number'], 1)

        # if you pass a run number in it is incremented
        setup_config_for_restarting_step(test)
        self.assertEqual(test['finalize_run_number'], 2)

        # if there is aready completed ids do not overwrite
        test['finalize_completed_ids'].append("test")
        setup_config_for_restarting_step(test)
        self.assertEqual(test['finalize_completed_ids'], ["test"])

    def test_break_to_restart_step(self):
        # if the config value for quit time is less than the current time it is false
        test = datetime.utcnow() + timedelta(seconds=100)
        self.assertEqual(break_to_restart_step(test), False)

        # the current quittime is greater than now it is true
        test = datetime.utcnow() - timedelta(seconds=100)
        self.assertEqual(break_to_restart_step(test), True)

    def test_finalize_is_complete(self):
        # if all the ids in one list are in the other it is complete
        test = {"ids": ["id1", "id2"], "finalize_completed_ids": ["id1", "id2"]}
        self.assertEqual(finalize_is_complete(test), True)

        # it does not matter the order
        test = {"ids": ["id1", "id2"], "finalize_completed_ids": ["id2", "id1"]}
        self.assertEqual(finalize_is_complete(test), True)

        # they must be the same ids
        test = {"ids": ["id1", "id2"], "finalize_completed_ids": ["id1", "otherid"]}
        self.assertEqual(finalize_is_complete(test), False)

        # missing is not true
        test = {"ids": ["id1", "id2"], "finalize_completed_ids": ["id1"]}
        self.assertEqual(finalize_is_complete(test), False)


if __name__ == '__main__':
    unittest.main()
