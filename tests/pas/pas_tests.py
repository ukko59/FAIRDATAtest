import time
import unittest

from tests.pas import pas
from tests.metax import metax
from utils import get_minimal_dataset_template, service_configured
from tests.pas.pas import (get_dataset, metax_user, metax_pwd,
                           get_contract, create_upload_user, upload_files,
                           create_file_metadata, delete_files)
from tests.ida import ida
import datetime
from parameterized import parameterized


@unittest.skipUnless(service_configured('PAS'),
                     'PAS not configured')
@unittest.skipUnless(service_configured('PAS'),
                     'PAS not configured')
@unittest.skipUnless(service_configured('METAX'), 'Metax not configured')
class TestPASMetax(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('Executing %s...' % cls.__name__)
        super().setUpClass()
#        metax.flush_project("2001036")

    def setUp(self):
        self.OK = [200, 201, 202]
        self.OK_404 = [200, 201, 202, 404]
        self.image_files = ['tiff', 'png', 'jpg', 'TIF']
        self.text_files = ['txt', 'html', 'csv', 'pdf']
        self.dataset_id = None
        self.files = None
        self.files_freezed_in_ida = False
        print("Test setup finished")

    def tearDown(self):
        print("In test teardown")
        if self.dataset_id:
            print('Deleting dataset: ' + str(self.dataset_id))
            status, response = metax.delete_dataset(self.dataset_id,
                                                    datasetuser=metax_user,
                                                    datasetpwd=metax_pwd)
            self.assertEqual(status, 204,
                             'Dataset delete fails: ' + str(response))
            print('Dataset ' + str(self.dataset_id) + ' deleted')
        if self.files_freezed_in_ida:
            self._unfreeze_files()
            print("Unfreeze finished")
        if self.files:
            delete_files()
            print("File deletion finished")
        print("Teardown finished")

    @parameterized.expand([
        ('files in ida files in dataset', 'ida', False),
        ('files in ida directory in dataset', 'ida', True),
        ('files locally files in dataset', 'pas', False),
        ('files locally directory in dataset', 'pas', True)
    ])
    def test_preserve_dataset(self, _, storage, directory):
        key, data = self._create_dataset_data(storage,
                                              directory
                                              )
        self._create_dataset_for_preservation(storage, key, data)
        self._assert_dataset_preservation()

    def _assert_dataset_preservation(self):
        print("Dataset id: " + str(self.dataset_id))
        status, response = pas.propose_dataset(self.dataset_id,
                                               'Proposing dataset')
        self.assertIn(
            status, self.OK, "Proposing dataset fails: " + str(response))
        status, response = get_dataset(self.dataset_id)
        self.assertIn(status, self.OK, "Get dataset fails")
        self.assertEqual(10, response.json()['passtate'],
                         'Proposing dataset fails')
        # generate metadata for the dataset
        print("Dataset proposed")
        status, response = pas.generate_metadata(self.dataset_id)
        self.assertIn(status, self.OK,
                      'Generating dataset metadata fails: ' + str(response))
        self.assertEqual(
            True, response.json()['success'],
            'Generating metadata for dataset fails: ' + str(
                response.json()['error']))
        print("Metadata generated")
        status, response = get_dataset(self.dataset_id)
        self.assertIn(status, self.OK, 'Get dataset fails: ' + str(response))
        self.assertEqual(20, response.json()['passtate'],
                         'Generating metadata for dataset fails')
        # validate the dataset
        status, response = pas.validate_metadata(self.dataset_id)
        self.assertIn(status, self.OK,
                      'Validating dataset fails: ' + str(response))
        self.assertEqual(True, response.json()['is_valid'],
                         'Validating dataset fails: ' + str(
                response.json()['error']))
        status, response = get_dataset(self.dataset_id)
        self.assertIn(status, self.OK, 'Get dataset fails: ' + str(response))
        self.assertEqual(70, response.json()['passtate'],
                         'Validating dataset fails')
        print("Metadata validated")
        # confirm the metadata of the dataset
        status, response = pas.confirm_dataset_metadata(self.dataset_id)
        self.assertIn(status,
                      self.OK, 'Confirming dataset fails: ' + str(response))
        self.assertEqual(str(self.dataset_id), response.json()['dataset_id'],
                         'Confirming dataset fails. Dataset id conflict')
        self.assertEqual(75, response.json()['passtate'],
                         'Confirming dataset fails. Passtate incorrect')
        status, response = get_dataset(self.dataset_id)
        self.assertIn(status, self.OK, 'Get dataset fails: ' + str(response))
        self.assertEqual(75, response.json()['passtate'],
                         'Confirming dataset fails: ' + str(response))
        print("Metadata confirmed")
        # accept the dataset for preservation
        status = pas.accept_dataset_for_preservation(self.dataset_id)
        self.assertIn(status, self.OK, 'Accepting dataset for dpres fails')
        status, response = get_dataset(self.dataset_id)
        self.assertIn(status, self.OK, 'Get dataset fails: ' + str(response))
        self.assertEqual(80, response.json()['passtate'],
                         'Accepting dataset for dpres fails: ' + str(response))
        print("Dataset accepted for preservation")
        # preserve the dataset
        status, response = pas.preserve_dataset(self.dataset_id)
        self.assertIn(status, self.OK, 'Preserving dataset fails')
        status, response = get_dataset(self.dataset_id)
        self.assertIn(status, self.OK, 'Get dataset fails: ' + str(response))
        self.assertEqual(80, response.json()['passtate'],
                         'Preserving dataset fails: ' + str(response))

        print("Waiting 10 minutes for preservation process to complete")
        for _i in range(60):
            status, response = get_dataset(self.dataset_id)
            self.assertIn(status,
                          self.OK, 'Get dataset fails: ' + str(response)
                          )
            passtate = response.json()['passtate']
            if passtate == 120 or passtate == 130:
                break
            time.sleep(10)
            print('.', end='', flush=True)
        self.assertEqual(
            120, passtate, 'Dataset details: passtateDescription=' +
            response.json()['passtateDescription'] + ', passtateReasonDesc=' +
            response.json()['passtateReasonDesc'])

    def _freeze_files(self):
        data = {
            "project": pas.project,
            "pathname": "/files"
        }
        status, response = ida.freeze_file(pas.project_user, data)
        self.assertIn(status, self.OK, 'freeze fails: ' + str(response))
        self.files_freezed_in_ida = True

        file_is_in_metax = pas.wait_until_directory_appears_in_metax(
            data['project'], data['pathname'])
        self.assertEqual(
            file_is_in_metax, True, 'Frozen file never appeared in metax')
        status, response = ida.get_frozen_node_action(pas.project_user,
                                                      response['pid'])
        self.assertIn(status, self.OK,
                      'Reading file details from IDA fails: ' + str(response))
        return response

    def _unfreeze_files(self):
        data = {
            "project": pas.project,
            "pathname": "/files"
        }

        for i in range(0, 20):
            status, _res = ida.unfreeze_file(pas.project_user, data)
            if status == 200:
                print('unfreeze success')
                break

            # It may take a moment for the previous freeze action to complete.
            # If the previous action is not completed, an unfreeze action too
            # soon will cause a conflicting-action error.
            time.sleep(1)
            if i % 5 == 0 and i > 0:
                print("unfreeze probably still conflicting with freeze" +
                      "action, waiting a bit...")

        self.assertIn(status, self.OK, 'Ida file unfreezing failed')

        file_disappeared_from_metax = \
            pas.wait_until_file_disappears_from_metax(data['project'],
                                                      data['pathname'])
        self.assertEqual(file_disappeared_from_metax,
                         True,
                         'Frozen file never disappeared from metax')

    def _map_file_json(self, file):
        if file["pathname"].split('.')[-1] in self.image_files:
            pl_en = "Image"
            pl_fi = "Kuva"
            pl_und = "Kuva"
        elif file["pathname"].split('.')[-1] in self.text_files:
            pl_en = "Text"
            pl_fi = "Teksti"
            pl_und = "Teksti"
        return {
            "title": "Title for " + file["pathname"],
            "identifier": file["pid"],
            "file_type": {
                "in_scheme": ("http://uri.suomi.fi/codelist/"
                              "fairdata/file_type"),
                "identifier": ("http://uri.suomi.fi/codelist/fairdata/"
                               "file_type/code/image"),
                "pref_label": {
                    "en": pl_en,
                    "fi": pl_fi,
                    "und": pl_und
                }
            },
            "use_category": {
                "in_scheme": ("http://uri.suomi.fi/codelist/fairdata/"
                              "use_category"),
                "identifier": ("http://uri.suomi.fi/codelist/fairdata/"
                               "use_category/code/source"),
                "pref_label": {
                    "en": "Source material",
                    "fi": "Lähdeaineisto",
                    "und": "Lähdeaineisto"
                }
            }
        }

    def _upload_files(self):
        response = create_upload_user()
        self.assertIn(response.status_code, self.OK,
                      'Creating upload user fails: ' + str(response.json()))
        response = delete_files()
        self.assertIn(response.status_code, self.OK_404,
                      'Deleting local files fails: ' + str(response.json()))
        response = upload_files()
        self.assertIn(response.status_code, self.OK,
                      "Uploading files fails: " + str(response))
        response = create_file_metadata()
        self.assertIn(response.status_code, self.OK,
                      "Creating file metadata fails: " + str(response))
        files = []
        for fil in response.json()['success']:
            files.append({
                'pid': fil['object']['identifier'],
                'pathname': fil['object']['file_path']})
        self.files = files
        return files

    def _create_dataset_data(self, storage, root_directory):
        if storage == 'ida':
            files = self._freeze_files()
        elif storage == 'pas':
            files = self._upload_files()
        if root_directory:
            file_id = files[0]['pid']
            key = 'directories'
            response = metax.get_file(file_id, fileuser=metax_user,
                                      filepwd=metax_pwd)
            self.assertIn(response.status_code, self.OK,
                          "Reading file fails: " + str(response))
            root_dir_id = self._get_root_dir(
                response.json()['parent_directory']['identifier'])
            data = [
                {
                    "identifier": root_dir_id,
                    "title": "Title for directory",
                    "use_category": {
                        "in_scheme": ("http://uri.suomi.fi/codelist/fairdata/"
                                      "use_category"),
                                      "identifier": (
                                           "http://uri.suomi.fi/"
                                            "codelist/fairdata/"
                                            "use_category/code/"
                                            "source"
                                        ),
                                       "pref_label": {
                                           "en": "Source material",
                                           "fi": "Lähdeaineisto",
                                           "und": "Lähdeaineisto"
                                        }
                                    }
                    }
            ]
        else:
            key = 'files'
            data = [self._map_file_json(file) for file in files]
        return key, data

    def _create_dataset_for_preservation(self, file_storage, key, data):
        response = get_contract()
        self.assertIn(response.status_code, self.OK,
                      "Metax get contract fails: " + str(response))
        contract_id = response.json()['id']

        dataset = get_minimal_dataset_template()
        dataset["research_dataset"]['files'] = []
        dataset["research_dataset"]['directories'] = []
        dataset["data_catalog"] = "urn:nbn:fi:att:data-catalog-" + file_storage
        dataset["editor"] = {
            "owner_id": "053d18ecb29e752cb7a35cd77b34f5fd",
            "creator_id": "053d18ecb29e752cb7a35cd77b34f5fd",
            "identifier": "qvain",
            "record_id": "100"
        }
        dataset["research_dataset"]["access_rights"]["restriction_grounds"] = [
                {
                    "identifier": ("http://uri.suomi.fi/codelist/fairdata/"
                                   "restriction_grounds/code/other"),
                    "pref_label": {
                        "fi": "Avoin, ei tiedossa olevia rajoituksia",
                        "und": "Avoin, ei tiedossa olevia rajoituksia"
                    }
                }
            ]
        dataset["version_notes"] = [
            "This version is initial version."
        ]
        dataset["research_dataset"]["provenance"] = [
            {
                "preservation_event": {
                    "in_scheme": ("http://uri.suomi.fi/codelist/fairdata/"
                                  "preservation_event"),
                    "identifier": ("http://uri.suomi.fi/codelist/fairdata/"
                                   "preservation_event/code/cre"),
                    "pref_label": {
                        "en": "Creation",
                        "fi": "Luonti",
                        "und": "Luonti"
                    }
                },
                "temporal": {
                    "start_date": "2018-06-01T17:41:59+03:00",
                    "end_date": "2018-06-02T17:41:59+03:00"
                },
                "description": {
                    "en": "Provenance description"
                }
            }
        ]
        dataset["research_dataset"]["publisher"] = {
            "name": {
                "fi": "School services, ARTS",
                "und": "School services, ARTS"
            },
            "@type": "Organization",
            "homepage": {
                "title": {
                    "en": "Publisher website",
                    "fi": "Julkaisijan kotisivu"
                },
                "identifier": "http://www.publisher.fi/"
            },
            "identifier": "http://uri.suomi.fi/codelist/fairdata/organization/code/10076-A800",
            "is_part_of": {
                "name": {
                    "en": "Aalto University",
                    "fi": "Aalto yliopisto",
                    "sv": "Aalto universitetet",
                    "und": "Aalto yliopisto"
                },
                "@type": "Organization",
                "homepage": {
                    "title": {
                        "en": "Publisher parent website",
                        "fi": "Julkaisijan yläorganisaation kotisivu"
                    },
                    "identifier": "http://www.publisher_parent.fi/"
                },
                "identifier": "http://uri.suomi.fi/codelist/fairdata/organization/code/10076"
            },
            "contributor_type": [
                {
                    "in_scheme": "http://uri.suomi.fi/codelist/fairdata/contributor_type",
                    "identifier": "http://uri.suomi.fi/codelist/fairdata/contributor_type/code/Distributor",
                    "pref_label": {
                        "en": "Distributor",
                        "fi": "Jakelija",
                        "sv": "Distributör",
                        "und": "Jakelija"
                    }
                }
            ]
        }
        st = datetime.datetime.fromtimestamp(time.time())
        time_stamp = str(st.replace(microsecond=0).isoformat()) + "+00:00"
        dataset['research_dataset']['modified'] = time_stamp
        dataset['research_dataset']['title']['en'] = (
            "Fairdata Integration Test Dataset " + time_stamp)
        dataset['research_dataset']['issued'] = "1997-02-21"
        dataset['research_dataset'][key] = data
        status, response = metax.create_dataset(dataset,
                                                datasetuser=metax_user,
                                                datasetpwd=metax_pwd)
        self.assertIn(status, self.OK,
                      'Metax create dataset fails: ' + str(response.json()))
        dataset = response.json()
        self.dataset_id = dataset['id']
        pas.set_dataset_contract(self.dataset_id, contract_id)
        status, response = metax.update_dataset(dataset['identifier'], dataset,
                                                datasetuser=metax_user,
                                                datasetpwd=metax_pwd)
        self.assertIn(status, self.OK,
                      'Adding files to dataset fails: ' + str(response))
        self._update_file_metadata()
        print("File metadata updated in Metax")

    def _update_file_metadata(self):
        response = metax.get_dataset_files(self.dataset_id,
                                           datasetuser=metax_user,
                                           datasetpwd=metax_pwd)
        self.assertIn(response.status_code, self.OK,
                      'Getting dataset files fails: ' + str(response))
        for file in response.json():
            if 'file_format' in file and 'csv' in file['file_format']:
                file_json = {}
                file_json['file_characteristics'] = {
                    "file_format": "text/csv",
                    "csv_delimiter": ",",
                    "csv_has_header": True,
                    "csv_record_separator": "LF",
                    "csv_quoting_char": "\""
                }
                response = metax.update_file(file['identifier'], file_json,
                                             fileuser=metax_user,
                                             filepwd=metax_pwd)
                self.assertIn(
                    response.status_code, self.OK,
                    'CSV file metadata update fails: ' + str(response.json()))

    def _get_root_dir(self, dir_id):
        response = metax.get_directory(dir_id, fileuser=metax_user,
                                       filepwd=metax_pwd)
        self.assertIn(response.status_code, self.OK,
                      "Reading directory fails: " + str(response))
        response_json = response.json()
        if response_json['directory_path'] != '/':
            self._get_root_dir(response_json['parent_directory']['identifier'])
        return dir_id
