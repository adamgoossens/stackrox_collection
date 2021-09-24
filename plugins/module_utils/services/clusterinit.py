from ansible.module_utils.urls import open_url
from http.client import HTTPException
import json
from typing import List, Dict

from ansible_collections.adamgoossens.stackrox.plugins.module_utils import exceptions

# some aliases for easy reading
InitBundleId = str
InitBundle = dict
ClusterId = str

class ClusterInitService:
    def __init__(self, token, central, validate_certs=True):
        self.token = token
        self.central = central
        self.validate_certs = validate_certs
        self.api_base = f"{central}/v1/cluster-init"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def __request(self, 
                  url_suffix='init-bundles', 
                  expect_code=200,
                  method='GET',
                  data=None):

        url = f"{self.api_base}/{url_suffix}"
        data_str = json.dumps(data) if data else None

        resp = open_url(url=url,
                        headers=self.headers,
                        validate_certs=self.validate_certs,
                        method=method,
                        data=data_str)

        if resp.status == 401:
            raise exceptions.UnauthorizedException(f"API token unauthorized for method {method} to URL {url}")

        if resp.status != expect_code:
            raise exceptions.StackroxApiException(f"Unexpected status code from Stackrox API. Expected = {expect_code}, received = {resp.status}")

        body = resp.read()
        return json.loads(body)

    def list_initbundles(self) -> List[InitBundle]:
        #
        # Return a list of all bundles
        #
        return self.__request()['items']

    def get_initbundle(self, name: str) -> InitBundle:
        #
        # Return the bundle identified by the given name.
        #
        # Returns None if no bundle is found.
        #
        all_bundles = self.list_initbundles()
        for bundle in all_bundles:
            if bundle['name'] == name:
                return bundle

        return None

    def create_initbundle(self, name: str) -> InitBundle:
        #
        # Create a bundle with the given name.
        #
        if type(name) != str:
            raise ValueError("Name must be a string")

        bundle = self.__request(
                    method='POST',
                    data={"name": name }
                 )

        return bundle

    def revoke_initbundles(self, 
                           bundle_ids: List[InitBundleId],
                           impacted_cluster_ids: List[ClusterId] = []) -> List[InitBundleId]:
        #
        # Delete the bundle identified by the given
        # bundle ID.
        #
        # bundle_ids may be a list of IDs or a string containing
        # a single ID.
        #

        bundle_ids = bundle_ids if type(bundle_ids) == list else [bundle_ids]

        if len(bundle_ids) == 0:
            raise ValueError("No init bundle IDs provided")

        # ensure we only have strings in the bundle and cluster ids
        for id in bundle_ids:
            if type(id) != str:
                raise ValueError("Bundle IDs must be strings")

        for id in impacted_cluster_ids:
            if type(id) != str:
                raise ValueError("Impacted cluster IDs must be strings")

        data = {
            "ids": bundle_ids,
            "confirmImpactedClusterIds": impacted_cluster_ids
        }

        result = self.__request(method="PATCH",
                                url_suffix="init-bundles/revoke",
                                data=data)

        # one or more bundle IDs failed to revoke
        if len(result['initBundleRevocationErrors']) > 0:
            raise exceptions.BundleRevokeFailedException(result['initBundleRevocationErrors'])

        return result['initBundleRevokedIds']
