from ansible.module_utils.basic import AnsibleModule
from ansible_collections.adamgoossens.stackrox.plugins.module_utils.services.clusterinit import ClusterInitService

import json

def run_module():
    module_args = dict(
        token=dict(type='str', required=True),
        central=dict(type='str', required=True),
        validate_certs=dict(type='bool', required=False),
        name=dict(type='str', required=True),
        state=dict(type='str', choices=['present','absent'], default='present')
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    service = ClusterInitService(
                token=module.params['token'],
                central=module.params['central'],
                validate_certs=module.params['validate_certs']
              )

    existing_bundle = service.get_initbundle(module.params['name'])

    if module.params['state'] == 'absent':
        if existing_bundle:
            impacted_cluster_ids = [cluster['id'] for cluster in existing_bundle['impactedClusters']]

            service.revoke_initbundles(
                        bundle_ids=[existing_bundle['id']],
                        impacted_cluster_ids=impacted_cluster_ids)
            result['changed'] = True
    else:
        if existing_bundle is None:
            existing_bundle = service.create_initbundle(name=module.params['name'])
            result['changed'] = True

        result['initbundle'] = existing_bundle

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
