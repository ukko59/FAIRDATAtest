
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
                "USER": "tpas",
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
        "PROJ_USER_PASS": "test",
    },

    "PAS":  {
        "HOST": "",
        "USERS": {
            # Basic authentication user accessing admin-rest-api
            "ADMIN-API": {
                "USER": "admin",
                "PASS": ""
            }
        }
    },

    "PAS_UPLOAD":  {
        "HOST": "",
        "USERS": {
            "ADMIN": {
                "USER": "admin",
                "PASS": ""
            }
        }
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
