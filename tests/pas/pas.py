import requests
import os.path
import json
from config import conf_vars
from tests.metax import metax
from time import sleep
import shutil
import tempfile

requests.packages.urllib3.disable_warnings()

project = 'pas_test_project'
project_user = 'pas_test_user'
upload_user = 'upload_user'
upload_user_pass = None

try:
    HOST = conf_vars['PAS']['HOST']
    UPLOAD_HOST = conf_vars['PAS_UPLOAD']['HOST']
    URL = 'https://%s/basicauth/api/1.0' % HOST
    UPLOAD_ADMIN_URL = 'https://%s/filestorage/api/v1/users' % UPLOAD_HOST
    UPLOAD_FILES_URL = 'https://%s/filestorage/api/v1/files' % UPLOAD_HOST
    UPLOAD_METADATA_URL = ('https://%s/filestorage/api/v1/metadata' %
                           UPLOAD_HOST)
    admin_auth = (conf_vars['PAS']['USERS']['ADMIN-API']['USER'],
                  conf_vars['PAS']['USERS']['ADMIN-API']['PASS'])
    metax_user = conf_vars['METAX']['USERS']['PAS']['USER']
    metax_pwd = conf_vars['METAX']['USERS']['PAS']['PASS']
    upload_admin = conf_vars['PAS_UPLOAD']['USERS']['ADMIN']['USER']
    upload_admin_pwd = conf_vars['PAS_UPLOAD']['USERS']['ADMIN']['PASS']
except Exception as e:
    print('Note: PAS not configured: ' + str(e))


def get_contract():
    """ Creates a contract if not already exists """
    contract_id = 'urn:uuid:abcd1234-abcd-1234-5678-abcd1234abcd'
    response = metax.get_contract(contract_id, datasetuser=metax_user,
                                  datasetpwd=metax_pwd)
    if response.status_code == 404:
        my_path = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(my_path, 'data/contract.json')) as f:
            contract_json = json.load(f)
            response = metax.create_contract(contract_json,
                                             datasetuser=metax_user,
                                             datasetpwd=metax_pwd)
    return response


def get_dataset(dataset_id, auth=admin_auth):
    """ Gets dataset as json object.
    :return: status code
    """
    r = requests.get('%s/datasets/%s' % (URL, dataset_id),
                     headers={'Content-Type': 'application/json'},
                     auth=auth, verify=False)
    return r.status_code, r


def set_dataset_contract(dataset_id, contract_id, auth=admin_auth):
    """ Gets dataset as json object.
    :return: status code
    """
    r = requests.post('%s/datasets/%s/contract' % (URL, dataset_id),
                      data={'identifier': contract_id}, auth=auth,
                      verify=False)
    return r.status_code


def propose_dataset(dataset_id, message='Proposing', auth=admin_auth):
    """ propose a dataset for digital preservation.
    :return: status code
    """
    r = requests.post('%s/datasets/%s/propose' % (URL, dataset_id),
                      data={'message': message}, auth=auth,
                      verify=False)
    return r.status_code, r


def generate_metadata(dataset_id, auth=admin_auth):
    """ Generate metadata for dataset.
    :return: status code
    """
    r = requests.post('%s/research/dataset/%s/genmetadata' % (URL, dataset_id),
                      headers={'Content-Type': 'application/json'},
                      auth=auth, verify=False)
    return r.status_code, r


def validate_metadata(dataset_id, auth=admin_auth):
    """ Validates the metadata of dataset.
    :return: status code
    """
    r = requests.post('%s/research/dataset/%s/validate' % (URL, dataset_id),
                      auth=auth, verify=False)
    return r.status_code, r


def confirm_dataset_metadata(dataset_id, auth=admin_auth):
    """ Confirm dataset metadata is valid for preservation.
    :return: status code
    """
    r = requests.post('%s/datasets/%s/confirm' % (URL, dataset_id),
                      data={'confirmed': 'true'}, auth=auth,
                      verify=False)
    return r.status_code, r


def accept_dataset_for_preservation(dataset_id, auth=admin_auth):
    """ Preserve a dataset in dpres.
    :return: status code
    """
    r = requests.post('%s/datasets/%s/preserve' % (URL, dataset_id),
                      auth=auth, verify=False)
    return r.status_code


def preserve_dataset(dataset_id, auth=admin_auth):
    """ Preserve a dataset in dpres.
    :return: status code
    """
    r = requests.post('%s/research/dataset/%s/preserve' % (URL, dataset_id),
                      auth=auth, verify=False)
    return r.status_code, r


def reject_dataset(dataset_id, auth=admin_auth):
    """ reject a dataset in dpres.
    :return: status code
    """
    r = requests.post('%s/datasets/%s/reject' % (URL, dataset_id),
                      auth=auth, verify=False)
    return r.status_code


def remove_dataset(dataset_id, auth=admin_auth):
    """ remove a dataset in dpres.
    :return: status code
    """
    r = requests.post('%s/datasets/%s/remove' % (URL, dataset_id),
                      auth=auth, verify=False)
    return r.status_code


def reset_dataset(dataset_id, auth=admin_auth):
    """ reset a dataset in dpres.
    :return: status code
    """
    r = requests.post('%s/datasets/%s/reset' % (URL, dataset_id),
                      auth=auth, verify=False)
    return r.status_code


def wait_until_directory_appears_in_metax(project, dir_path, timeout=30):
    """
    When freezing directory, it takes a while for a directory to appear in
    metax.
    """
    print('Waiting until directory appears in metax...')
    for i in range(0, timeout):
        if metax.find_directory_by_project_and_path(project, dir_path,
                                                    fileuser=metax_user,
                                                    filepwd=metax_pwd):
            print('Found the directory!')
            return True
        sleep(2)
        if i % 5 == 0 and i > 0:
            print('Still didnt find...')
    return False


def wait_until_file_disappears_from_metax(project, file_path, timeout=30):
    """
    When unfreezing/deleting files, it takes a while for a file to be removed
    from metax.
    """
    print('Waiting until file disappears from metax...')
    for i in range(0, timeout):
        if not metax.find_file_by_project_and_path(project, file_path,
                                                   fileuser=metax_user,
                                                   filepwd=metax_pwd):
            print('File is gone!')
            return True
        sleep(1)
        if i % 5 == 0 and i > 0:
            print('File still not gone...')
    return False


def create_upload_user():
    """ Create user and project for uploading files.
    :return: status code
    """
    url = '%s/%s' % (UPLOAD_ADMIN_URL, upload_user)
    print(url)
    r = requests.delete(url,
                        auth=(upload_admin, upload_admin_pwd), verify=False)
    if r.status_code == 200 or r.status_code == 404:
        r = requests.post(
            '%s/%s/%s' % (UPLOAD_ADMIN_URL, upload_user, project),
            auth=(upload_admin, upload_admin_pwd), verify=False)
        if r.status_code == 200:
            global upload_user_pass
            upload_user_pass = r.json()['password']
    return r


def upload_files():
    my_path = os.path.abspath(os.path.dirname(__file__))
    try:
        zip_file = shutil.make_archive(
            'pictures', 'zip',
            root_dir=os.path.join(my_path, 'data'),
            base_dir='files')
        file_stream = open(zip_file, 'rb')
        response = requests.post(UPLOAD_FILES_URL + '/pictures.zip',
                                 data=file_stream,
                                 auth=(upload_user, upload_user_pass),
                                 verify=False)
        return response
    finally:
        file_stream.close()
        os.remove(zip_file)


def create_file_metadata():
    response = requests.post(UPLOAD_METADATA_URL + '/*',
                             auth=(upload_user, upload_user_pass),
                             verify=False)
    return response


def delete_files():
    response = requests.delete(UPLOAD_FILES_URL,
                               auth=(upload_user, upload_user_pass),
                               verify=False)
    return response
