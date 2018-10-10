#########
# Copyright (c) 2018 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

import os

from dsl_parser import tasks, constants
from manager_rest.test.base_test import BaseServerTestCase
from manager_rest.resolver_with_catalog_support import \
    ResolverWithCatalogSupport


TEST_PACKAGE_NAME = 'cloudify-script-plugin'
TEST_PACKAGE_VERSION = '1.2'


class TestParseWithResolver(BaseServerTestCase):
    def test_successful_plugin_import_resolver(self):
        dsl_location = os.path.join(
            self.get_blueprint_path('mock_blueprint'),
            'blueprint_with_plugin_import.yaml')

        resolver = ResolverWithCatalogSupport()
        self.upload_plugin(TEST_PACKAGE_NAME, TEST_PACKAGE_VERSION)

        plan = tasks.parse_dsl(dsl_location=dsl_location,
                               resources_base_path=self.tmpdir,
                               resolver=resolver)
        self.assertIsNone(plan[constants.DEPLOYMENT_PLUGINS_TO_INSTALL])
        deployment_plugins_to_install_for_node = \
            plan['nodes'][0][constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(1, len(deployment_plugins_to_install_for_node))
        plugin = deployment_plugins_to_install_for_node[0]
        self.assertEquals(TEST_PACKAGE_NAME, plugin['name'])

        # check the property on the plan is correct
        deployment_plugins_to_install_for_plan = \
            plan[constants.DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(1, len(deployment_plugins_to_install_for_plan))

    def test_success_with_blueprint_import_resolver(self):
        blueprint_id = 'imported_blueprint'
        self.put_blueprint('mock_blueprint',
                           'blueprint.yaml', blueprint_id)

        # The real testing
        dsl_location = os.path.join(
            self.get_blueprint_path('mock_blueprint'),
            'blueprint_with_blueprint_import.yaml')

        resolver = ResolverWithCatalogSupport()

        plan = tasks.parse_dsl(dsl_location=dsl_location,
                               resources_base_path=self.tmpdir,
                               resolver=resolver)

        nodes = set([node["name"] for node in plan[constants.NODES]])

        self.assertEqual(nodes, set(["test", "vm", "http_web_server"]))
