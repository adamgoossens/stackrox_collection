from ansible_collections.adamgoossens.stackrox.plugins.modules import initbundle
from ansible_collections.adamgoossens.stackrox.plugins.module_utils.services.clusterinit import ClusterInitService

from ansible_collections.adamgoossens.stackrox.tests.unit.plugins.modules import utils
import json

from unittest.mock import Mock

class TestInitBundleModule(utils.ModuleTestCase):

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(utils.AnsibleFailJson):
            initbundle.main()

    @utils.patch('ansible_collections.adamgoossens.stackrox.plugins.modules.initbundle.ClusterInitService', autospec=True)
    def test_module_state_present_with_new_initbundle(self, cis_mock_class):
        #
        # We expect the module to:
        #
        # - attempt to fetch a matching initbundle by name, using ClusterInitService.get
        # - when no match is found, call create_initbundle with the correct name.
        # - return the resulting bundle to the caller
        #
        cis_mock = cis_mock_class.return_value

        bundle = utils.create_fake_initbundle(is_new=True)

        cis_mock.get_initbundle.return_value = None
        cis_mock.create_initbundle.return_value = bundle

        utils.set_module_args({
            **self.default_args,
            "state": "present",
            "name": bundle['meta']['name']
        })

        # execute
        with self.assertRaises(utils.AnsibleExitJson) as result:
            initbundle.main()

        self.assertTrue(result.exception.args[0]['changed'])
        self.assertEqual(result.exception.args[0]['initbundle'], bundle)
        cis_mock.get_initbundle.assert_called_with(name=bundle['meta']['name'])
        cis_mock.create_initbundle.assert_called_with(name=bundle['meta']['name'])   

    @utils.patch('ansible_collections.adamgoossens.stackrox.plugins.modules.initbundle.ClusterInitService', autospec=True)
    def test_module_state_present_with_existing_initbundle(self, cis_mock_class):
        #
        # We expect the module to check for an existing bundle and, when found,
        # return the bundle metadata and *not* attempt creating a new one
        #
        cis_mock = cis_mock_class.return_value

        bundle = utils.create_fake_initbundle(is_new=False)
        cis_mock.get_initbundle.return_value = bundle

        utils.set_module_args({
            **self.default_args,
            "state": "present",
            "name": bundle['name']
        })

        with self.assertRaises(utils.AnsibleExitJson) as result:
            initbundle.main()

        cis_mock.get_initbundle.assert_called_with(bundle['name'])
        cis_mock.create_initbundle.assert_not_called()
        self.assertFalse(result.exception.args[0]['changed'])
        self.assertEqual(result.exception.args[0]['initbundle'], bundle)

    @utils.patch('ansible_collections.adamgoossens.stackrox.plugins.modules.initbundle.ClusterInitService', autospec=True)
    def test_module_state_absent(self, cis_mock_class):
        # 
        # We expect the module to check if the bundle exists,
        # if found, call revoke_initbundles with the ID of the bundle
        # and all affected cluster IDs.
        #
        # If not, do nothing.
        #
        cis_mock = cis_mock_class.return_value

        bundle = utils.create_fake_initbundle(is_new=False)
        impacted_cluster_ids = [ cluster['id'] for cluster in bundle['impactedClusters'] ]

        cis_mock.get_initbundle.return_value = bundle
        cis_mock.revoke_initbundles.return_value = [bundle['id']]

        utils.set_module_args({
            **self.default_args,
            "state": "absent",
            "name": bundle['name']
        })

        with self.assertRaises(utils.AnsibleExitJson) as result:
            initbundle.main()

        # check correct use of the Service API
        cis_mock.revoke_initbundles.assert_called_with(
                            bundle_ids=[bundle['id']],
                            impacted_cluster_ids=impacted_cluster_ids)
        self.assertTrue(result.exception.args[0]['changed'])

        # reset for next test - non-existing bundle
        cis_mock.reset_mock()
        cis_mock.get_initbundle.return_value = None

        with self.assertRaises(utils.AnsibleExitJson) as result:
            initbundle.main()

        cis_mock.get_initbundle.assert_called_with(name=bundle['name'])
        cis_mock.revoke_initbundles.assert_not_called()
        self.assertFalse(result.exception.args[0]['changed'])
