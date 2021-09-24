import unittest
from unittest.mock import patch
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes
import json
import uuid
import base64

from datetime import datetime

def create_fake_initbundle(name = None, is_new = False):
    #
    # Create a fake initbundle structure, per what would come
    # back from the API
    #
    name = "cluster-" + str(uuid.uuid4()).split('-')[0] if name is None else name

    meta = {
        "id": str(uuid.uuid4()),
        "name": name,
        "createdAt": datetime.now().isoformat() + "Z",
        "expiresAt": datetime.now().isoformat() + "Z",
        "createdBy": {
            "attributes": [
                {
                    "key": "role",
                    "value": "Admin"
                },
                {
                    "key": "name",
                    "value": "module"
                }
            ],
            "authProviderId": "https://stackrox.io/jwt-sources#api-tokens",
            "id": "auth-token:fd41f355-9a24-4d48-af94-d3675db3f613"
        }
    }

    # new init bundles have no impacted clusters
    # put the metadata under a 'meta' key
    # and return some random helm/kubectl secrets
    if is_new:
        meta['impactedClusters'] = []
        helm = base64.b64encode(str(uuid.uuid4()).encode('ascii')).decode('ascii')
        kubectl = base64.b64encode(str(uuid.uuid4()).encode('ascii')).decode('ascii')

        item = {}
        item['meta'] = meta
        item['helmValuesBundle'] = helm
        item['kubectlBundle'] = kubectl

    else:
        # add a couple of impacted clusters.
        # note: no helm or kubectl data here.
        meta['impactedClusters'] = [
            { "name": "impacted-cluster-1", "id": str(uuid.uuid4()) },
            { "name": "impacted-cluster-2", "id": str(uuid.uuid4()) }
        ]

        item = {**meta}

    return item

def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)

class AnsibleExitJson(Exception):
    pass

class AnsibleFailJson(Exception):
    pass

def exit_json(*args, **kwargs):
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)

def fail_json(*args, **kwargs):
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)

class ModuleTestCase(unittest.TestCase):

    def setUp(self):
        self.default_args = {
            "central": "https://central.com",
            "token": "doesnotmatter"
        }

        self.mock_module = patch.multiple(basic.AnsibleModule,
                                          exit_json=exit_json,
                                          fail_json=fail_json)
        self.mock_module.start()
        set_module_args({})
        self.addCleanup(self.mock_module.stop)
