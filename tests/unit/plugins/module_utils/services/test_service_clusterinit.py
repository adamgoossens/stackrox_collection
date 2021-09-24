from ansible_collections.adamgoossens.stackrox.plugins.module_utils.services import clusterinit
from ansible_collections.adamgoossens.stackrox.plugins.module_utils import exceptions

import ansible.module_utils.urls
import unittest
from unittest.mock import patch
import json
import http
import uuid
import base64
from datetime import datetime

class TestClusterInitService(unittest.TestCase):

    def __generate_fake_bundle(self, name=None, new_bundle=False):
        #
        # Generate a fake bundle structure suitable for sending to the API
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
        if new_bundle:
            meta['impactedClusters'] = []
            helm = base64.b64encode(str(uuid.uuid4()).encode('ascii')).decode('ascii')
            kubectl = base64.b64encode(str(uuid.uuid4()).encode('ascii')).decode('ascii')

            item = {}
            item['meta'] = meta
            item['helmValuesBundle'] = helm
            item['kubectlBundle'] = kubectl

        else:
            # add a couple of impacted clusters.
            # note: no helm or kubectle data here.
            meta['impactedClusters'] = [
                { "name": "impacted-cluster-1", "id": str(uuid.uuid4()) },
                { "name": "impacted-cluster-2", "id": str(uuid.uuid4()) }
            ]

            item = {**meta}

        return item

    def __create_clusterinit_service(self):
        token = str(uuid.uuid4())
        central = 'https://central.com'
        headers= {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        cis = clusterinit.ClusterInitService(token=token, central=central)
        return (cis, token, central, headers)

    @patch('ansible_collections.adamgoossens.stackrox.plugins.module_utils.services.clusterinit.open_url')
    def test_request_throws_exception_on_unexpected_status(self, open_url):
        #
        # Ensure that if we get an unexpected status code from the
        # stackrox API that we raise a StackroxApiException.
        #
        stream = open_url.return_value
        stream.status = 123
        (service, token, central, headers) = self.__create_clusterinit_service()
        with self.assertRaises(exceptions.StackroxApiException):
            service.list_initbundles()

    @patch('ansible_collections.adamgoossens.stackrox.plugins.module_utils.services.clusterinit.open_url')
    def test_list_calls_api_correctly(self, open_url):
        #
        # Ensure that we can list bundles returned from the API
        # correctly.
        #
        bundle1 = self.__generate_fake_bundle()
        bundle2 = self.__generate_fake_bundle()
        bundle3 = self.__generate_fake_bundle()

        stream = open_url.return_value
        stream.status = 200
        stream.read.return_value = json.dumps({"items":[bundle1, bundle2, bundle3]})

        (service, token, central, expect_headers) = self.__create_clusterinit_service()

        results = service.list_initbundles()
        open_url.assert_called_with(url=f"{central}/v1/cluster-init/init-bundles",
                                    method='GET',
                                    validate_certs=True,
                                    headers=expect_headers,
                                    data=None)

        for expected_bundle in [bundle1, bundle2, bundle3]:
            self.assertIn(expected_bundle, results)

    @patch('ansible_collections.adamgoossens.stackrox.plugins.module_utils.services.clusterinit.open_url')
    def test_create_initbundle_uses_api_correctly(self, open_url):
        #
        # Ensure we can create init bundles correctly.
        #
        # what we'll get back from the 'api'
        return_bundle = self.__generate_fake_bundle(
                            name="new-cluster",
                            new_bundle=True
                        )

        stream = open_url.return_value
        stream.status = 200
        stream.read.return_value = json.dumps(return_bundle)

        (service, token, central, expect_headers) = self.__create_clusterinit_service()
  
        # the test
        new_bundle = service.create_initbundle(name="new-bundle")

        # make sure the API was called correctly
        open_url.assert_called_with(url=f"{central}/v1/cluster-init/init-bundles",
                                    method='POST',
                                    validate_certs=True,
                                    headers=expect_headers,
                                    data=json.dumps({"name": "new-bundle"}))

        # verify the returned bundle
        self.assertEqual(new_bundle, return_bundle)

    @patch('ansible_collections.adamgoossens.stackrox.plugins.module_utils.services.clusterinit.open_url')
    def test_revoke_initbundle_uses_api_correctly(self, open_url):
        #
        # Ensure the delete call is PATCH'ing appropriately.
        #
        
        bundle_ids_to_revoke = [
            str(uuid.uuid4())
        ]

        expected_body = {
            "ids": bundle_ids_to_revoke,
            "confirmImpactedClusterIds": []
        }

        delete_response = {
            "initBundleRevocationErrors": [],
            "initBundleRevokedIds": bundle_ids_to_revoke
        }

        (service, token, central, expect_headers) = self.__create_clusterinit_service()

        stream = open_url.return_value
        stream.status = 200
        stream.read.return_value = json.dumps(delete_response)

        revoked_ids = service.revoke_initbundles(bundle_ids_to_revoke)

        open_url.assert_called_with(
                    url=f"{central}/v1/cluster-init/init-bundles/revoke",
                    method="PATCH",
                    data=json.dumps(expected_body),
                    headers=expect_headers,
                    validate_certs=True
                 )

        self.assertEqual(revoked_ids, bundle_ids_to_revoke)

    @patch('ansible_collections.adamgoossens.stackrox.plugins.module_utils.services.clusterinit.open_url')
    def test_revoke_initbundle_throws_on_revocation_errors(self, open_url):
        bundle_id_to_revoke = str(uuid.uuid4())
        failed_response = {
            "initBundleRevokedIds": [],
            "initBundleRevocationErrors": [{
                "id": bundle_id_to_revoke,
                "error": "revoking init bundle: init bundle does not exist",
                "impactedClusters": []
            }]
        }

        stream = open_url.return_value
        stream.status = 200
        stream.read.return_value = json.dumps(failed_response)
       
        (service, token, central, expect_headers) = self.__create_clusterinit_service()

        with self.assertRaises(exceptions.BundleRevokeFailedException):
           service.revoke_initbundles(bundle_id_to_revoke)

    def test_revoke_initbundle_throws_on_bad_id_types(self):
        #
        # We only accept strings as bundle or cluster IDs.
        #
        (service, token, central, expect_headers) = self.__create_clusterinit_service()

        with self.assertRaises(ValueError):
            service.revoke_initbundles(bundle_ids=[1,2,3,4])

        with self.assertRaises(ValueError):
            service.revoke_initbundles(bundle_ids=['string'], impacted_cluster_ids=[1,2,3,4])

