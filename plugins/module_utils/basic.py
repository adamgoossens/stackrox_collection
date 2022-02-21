from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
from http.client import HTTPException
import json

class StackroxModule(AnsibleModule):
    def __init__(self, **kwargs):
        module_args = dict(
            token=dict(type='str', required=False, no_log=True),
            username=dict(type='str', required=False),
            password=dict(type='str', required=False, no_log=True),
            central=dict(type='str', required=True),
            validate_certs=dict(type='bool', required=False)
        )

        required_together = [ ('username', 'password') ]

        kwargs['argument_spec'] = {**module_args, **(kwargs.get('argument_spec', {})) }
        kwargs['required_together'] = kwargs.get('required_together', []) + required_together

        super().__init__(**kwargs)

class StackroxService:
    def __init__(self, api_base, token, username, password, central, validate_certs=True, **kwargs):
        self.token = token
        self.username = username
        self.password = password
        self.central = central
        self.validate_certs = validate_certs
        self.api_url = f"{central}/v1/{api_base}"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # only if using a token.
        # username/password forces basic auth
        if token:
            self.headers['Authorization'] = f"Bearer {token}"

    def _request(self, 
                  url_suffix='',
                  query_string='',
                  expect_code=200,
                  method='GET',
                  data=None):

        if url_suffix:
            url = f"{self.api_url}/{url_suffix}"
        else:
            url = self.api_url

        if query_string:
            url = f"{url}?{query_string}"

        extra_args = {}
        if not self.token:
            extra_args = { "url_username": self.username, "url_password": self.password, "force_basic_auth": True }

        data_str = json.dumps(data) if data else None

        resp = open_url(url=url,
                        headers=self.headers,
                        validate_certs=self.validate_certs,
                        method=method,
                        data=data_str,
                        **extra_args)

        if resp.status != expect_code:
            raise Exception(f"Unexpected status code from Stackrox API. Expected = {expect_code}, received = {resp.status}")

        body = resp.read()
        return json.loads(body)
