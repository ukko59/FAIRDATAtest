import time

import requests

from config import conf_vars


try:
    metax_host = conf_vars["METAX"]['HOST']
    datasetuser = conf_vars["METAX"]['USERS']['ETSIN']['USER']
    datasetpwd = conf_vars["METAX"]['USERS']['ETSIN']['PASS']
    fileuser = conf_vars["METAX"]['USERS']['IDA']['USER']
    filepwd = conf_vars["METAX"]['USERS']['IDA']['PASS']
    URL_datasets = "https://%s/rest/datasets" % metax_host
    URL_files = "https://%s/rest/files" % metax_host
    URL_contracts = "https://%s/rest/contracts" % metax_host
    URL_files_rpc = "https://%s/rpc/files" % metax_host
    URL_directories = "https://%s/rest/directories" % metax_host
except Exception as e:
    print('Note: Metax not configured (requires users: etsin, ida)')

# constants
TIMEOUT = 10


def create_dataset(dataset_json,
                   datasetuser=datasetuser,
                   datasetpwd=datasetpwd):
    """ Create a dataset in MetaX.
    :return: metax-id of the created dataset.
    """
    resp = requests.post(URL_datasets,
                         headers={'Content-Type': 'application/json'},
                         json=dataset_json,
                         auth=(datasetuser, datasetpwd),
                         timeout=TIMEOUT,
                         verify=False)
    return resp.status_code, resp


def update_dataset(urn, dataset_json, datasetuser=datasetuser,
                   datasetpwd=datasetpwd):
    r = requests.put(URL_datasets + '/{id}'.format(id=urn),
                     headers={'Content-Type': 'application/json'},
                     json=dataset_json,
                     auth=(datasetuser, datasetpwd),
                     timeout=TIMEOUT,
                     verify=False)
    time.sleep(10)
    # print(r.json()['next_version'])
    return r.status_code, r


def delete_dataset(urn, datasetuser=datasetuser, datasetpwd=datasetpwd):
    """ Delete a dataset from MetaX. """

    r = requests.delete(URL_datasets + '/{id}'.format(id=urn),
                        auth=(datasetuser, datasetpwd), timeout=TIMEOUT,
                        verify=False)
    # time.sleep(40)
    return r.status_code, r


def create_contract(contract_json, datasetuser=datasetuser,
                    datasetpwd=datasetpwd):
    """ Create a contract in MetaX.
    :return: response of POST
    """
    return requests.post(URL_contracts,
                         headers={'Content-Type': 'application/json'},
                         json=contract_json,
                         auth=(datasetuser, datasetpwd),
                         timeout=TIMEOUT,
                         verify=False)


def get_contract(contract_id, datasetuser=datasetuser, datasetpwd=datasetpwd):
    """ get a contract from MetaX. """

    return requests.get(URL_contracts + '/{id}'.format(id=contract_id),
                        auth=(datasetuser, datasetpwd),
                        timeout=TIMEOUT,
                        verify=False)


def get_file(file_id, fileuser=fileuser, filepwd=filepwd):
    """ get a file from MetaX. """

    return requests.get(URL_files + '/{id}'.format(id=file_id),
                        auth=(fileuser, filepwd), timeout=TIMEOUT,
                        verify=False)


def get_dataset_files(dataset_id, datasetuser=datasetuser,
                      datasetpwd=datasetpwd):
    """ get a file from MetaX. """

    return requests.get(URL_datasets + '/{id}'.format(id=dataset_id) + '/files',
                        auth=(datasetuser, datasetpwd), timeout=TIMEOUT,
                        verify=False)


def update_file(file_id, file_json, fileuser=fileuser, filepwd=filepwd):
    """ get a file from MetaX. """

    r = requests.patch(URL_files + '/{id}'.format(id=file_id),
                       headers={'Content-Type': 'application/json'},
                       json=file_json,
                       auth=(fileuser, filepwd),
                       timeout=TIMEOUT,
                       verify=False)
    time.sleep(2)
    return r


def get_directory(directory_id, fileuser=fileuser, filepwd=filepwd):
    """ get a directory from MetaX. """

    return requests.get(URL_directories + '/{id}'.format(id=directory_id),
                        auth=(fileuser, filepwd), timeout=TIMEOUT,
                        verify=False)


def find_file_by_project_and_path(project, file_path, fileuser=fileuser,
                                  filepwd=filepwd):
    resp = requests.get(
        '%s?project_identifier=%s&limit=1000000&fields=file_path' % (URL_files,
                                                                     project),
        auth=(fileuser, filepwd), timeout=TIMEOUT, verify=False)
    if resp.status_code == 200:
        for file in resp.json()['results']:
            if file['file_path'].startswith(file_path):
                return True
    return False


def find_directory_by_project_and_path(project, dir_path, fileuser=fileuser,
                                       filepwd=filepwd):
    resp = requests.get('%s/root?project=%s&limit=1000000' % (URL_directories,
                        project), auth=(fileuser, filepwd), timeout=TIMEOUT,
                        verify=False)
    if resp.status_code == 200:
        for directory in resp.json()['directories']:
            if directory['directory_path'] == dir_path:
                return True
    return False


def flush_project(pname):
    """ flush all the files related to particular project """

    resp = requests.post('%s/flush_project/%s' % (URL_files_rpc, pname),
                         auth=(fileuser, filepwd), timeout=TIMEOUT,
                         verify=False)
    if resp.status_code not in (200, 204):
        print('Warning: Metax failed to flush project %s. Reason: %s' % (pname,
                                                                         str(resp.content)))
    return resp.status_code
