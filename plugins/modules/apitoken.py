from ansible_collections.community.stackrox.plugins.module_utils.basic import StackroxModule
from ansible_collections.community.stackrox.plugins.module_utils.services.apitoken import Service

import json

def run_module():
    module_args = dict(
        name=dict(type='str', required=False),
        id=dict(type='str', required=False),
        role=dict(type='str', required=False),
        include_revoked=dict(type='bool', required=False, default=False),
        force_new=dict(type='bool', required=False, default=False),
        state=dict(type='str', choices=['present','absent', 'list', 'get'], default='present')
    )

    result = dict(
        changed=False,
        tokens=[]
    )

    module = StackroxModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ['name']),
            ('state', 'present', ['role']),
            ('state', 'absent', ['name', 'id'], True)
        ],
        supports_check_mode=False
    )

    service = Service(**module.params)

    if module.params['state'] == 'list':
        result['tokens'] = service.list(include_revoked=module.params['include_revoked'])

    elif module.params['state'] == 'get':
        result['tokens'] = service.get(name=module.params['name'], 
                                       id=module.params['id'],
                                       include_revoked=module.params['include_revoked'])

    else:
        # create or delete token
        existing_token = service.get(id=module.params['id'], name=module.params['name'])

        # make sure that if we're revoking tokens, and the user passes a name only,
        # that we only get one possible option.
        #
        # If we get several possible tokens, then we don't know which one to revoke.
        #
        if module.params['state'] == 'absent':
            if len(existing_token) > 0:
                module.fail_json(msg=f"Multiple tokens were found for the name provided. Cannot revoke. Use token ID instead.")

            if len(existing_token) == 1:
                service.revoke_token(id=existing_token['id'])
                result['changed'] = True

            # if len == 0 then nothing to do.
        else:
            # new token
            if len(existing_token) == 0:

                new_token = service.create(
                                        name=module.params['name'],
                                        role=module.params['role']
                            )
                existing_token = [new_token]
                result['changed'] = True

            # there is no updating to be done with tokens, so we need no other logic.

            result['tokens'] = existing_token

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
