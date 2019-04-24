import time
import unittest

from tests.etsin import etsin
from tests.metax import metax
from utils import get_minimal_dataset_template, service_configured


@unittest.skipUnless(service_configured('ETSIN'), 'Etsin not configured')
@unittest.skipUnless(service_configured('METAX'), 'Metax not configured')
class TestEtsinMetax(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('Executing %s...' % cls.__name__)
        super().setUpClass()

    def setUp(self):
        self.OK = [200, 201, 202, 203, 204]
        self.FAIL = [401, 403, 404]

    def test_create_dataset(self):
        # loading the example dataset

        data = get_minimal_dataset_template()
        status, cdata = metax.create_dataset(data)

        self.assertIn(status, self.OK,
                      "could not create dataset: " + str(cdata))
        urn = cdata.json()["identifier"]
        time.sleep(10)

        etsin_status, etsin_data = etsin.view_dataset(urn)
        self.assertIn(etsin_status, self.OK, "Etsin could not found the dataset")

    def test_update_dataset(self):
        data = get_minimal_dataset_template()
        status, response = metax.create_dataset(data)
        self.assertIn(status, self.OK,
                      "could not create dataset: " + str(response))
        dataset = response.json()
        dataset['research_dataset']['title']['en'] = 'title updated'
        status, response = metax.update_dataset(dataset['id'], dataset)
        self.assertIn(status, self.OK, "Metax update failure")
        updated_data = response.json()
        urn = updated_data["identifier"]
        etsin_status, etsin_data = etsin.view_dataset(urn)
        self.assertIn(etsin_status, self.OK, "Etsin failure")

    def test_delete_dataset(self):
        data = get_minimal_dataset_template()

        status, response = metax.create_dataset(data)
        self.assertIn(status, self.OK,
                      "could not create dataset: " + str(response))
        cdata = response.json()
        urn = cdata["identifier"]

        time.sleep(2)
        status, response = metax.delete_dataset(cdata['id'])
        self.assertIn(status, self.OK,
                      "Metax dataset delete failure: " + str(response))

        etsin_status, etsin_data = etsin.view_dataset(urn)
        # this assert makes no sense, since a deleted dataset will have a tombstone page anyway?
        # check status in some other way.
        # self.assertIn(etsin_status, self.FAIL, "Etsin found the deleted dataset")
