
conf_vars = {

    "METAX":  {
        "HOST": "",
        "USERS": {
            "METAX": {
                "USER": "",
                "PASS": "",
            },
            "ETSIN": {
                "USER": "",
                "PASS": "",
            },
            "QVAIN": {
                "USER": "",
                "PASS": "",
            },
            "PAS": {
                "USER": "",
                "PASS": ""
            }
        }
    },

    "ETSIN":  {
        "HOST": "",
    },

    "IDA":  {
        "HOST": "",
        "USERS": {
            "SSH_USER": {
                "USER": "",
                "PASS": "",
            },
        },
        # other required confs
        "HTTPD_USER": "apache",
        "ROOT_DIR": "/var/ida",
        "PROJECT": "",
        "PROJ_USER": "",
        "PROJ_USER_PASS": "test",
    },

    "PAS":  {
        "HOST": "",
        "USER": "",
        "PASS": "",
    },

    "PAS_UPLOAD":  {
        "HOST": "",
        "USERS": {
            "ADMIN": {
                "USER": "admin",
                "PASS": ""
            },
            "USER": {
                "USER": "integration_test_upload_user",
            }
        },
        "PROJECT": "integration_test_upload_project"
    },

    "QVAIN":  {
        "HOST": "",
        "TOKEN": "",
        "SID": ""
    },

    "DOWNLOAD": {
        "HOST": ""
    },

}
