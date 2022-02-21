from ansible.module_utils.urls import open_url
from http.client import HTTPException
import json
from typing import List, Dict

from ansible_collections.community.stackrox.plugins.module_utils.basic import StackroxService
from ansible_collections.community.stackrox.plugins.module_utils import exceptions

class Service(StackroxService):
    def __init__(self, **kwargs):
        kwargs['api_base'] = 'cluster-init'
        super().__init__(**kwargs)

    def list_initbundles(self):
        #
        # Return a list of all bundles
        #
        res = self._request(
                url_suffix='init-bundles'
              )

        return res['items']

    def get_initbundle(self, name):
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

    def create_initbundle(self, name):
        #
        # Create a bundle with the given name.
        #
        bundle = self._request(
                    url_suffix='init-bundles',
                    method='POST',
                    data={"name": name}
                 )

        return bundle

    def revoke_initbundles(self, 
                           bundle_ids,
                           impacted_cluster_ids):
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

        result = self._request(method="PATCH",
                                url_suffix="init-bundles/revoke",
                                data=data)

        # one or more bundle IDs failed to revoke
        if len(result['initBundleRevocationErrors']) > 0:
            raise exceptions.BundleRevokeFailedException(result['initBundleRevocationErrors'])

        return result['initBundleRevokedIds']
