from ansible.module_utils.basic import AnsibleModule
from ansible_collections.adamgoossens.stackrox.plugins.module_utils.services.clusterinit import ClusterInitService

import json
import requests
import sys

def run_module():
    module_args = dict(
        token=dict(type='str', required=True),
        central=dict(type='str', required=True),
        validate_certs=dict(type='bool', required=False)
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    service = ClusterInitService(token=module.params['token'],
                                 central=module.params['central'],
                                 validate_certs=module.params['validate_certs'])

    result['bundles'] = service.list_initbundles()

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
