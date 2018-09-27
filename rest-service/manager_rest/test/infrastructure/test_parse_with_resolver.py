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

from dsl_parser import tasks
from dsl_parser import (constants, models)
from manager_rest.test.base_test import BaseServerTestCase
from manager_rest.app_context import ResolverWithPlugins
from manager_rest.manager_exceptions import (InvalidPluginError,
                                             NotFoundError)


TEST_PACKAGE_NAME = 'cloudify-script-plugin'
TEST_PACKAGE_VERSION = '1.2'


class TestPluginParseWithResolver(BaseServerTestCase):
    def test_successful_plugin_import_resolver(self):

        dsl_location = os.path.join(
            '../.',
            'mock_blueprint',
            'blueprint_with_plugin_import.yaml')

        resolver = ResolverWithPlugins()
        self.upload_plugin(TEST_PACKAGE_NAME, TEST_PACKAGE_VERSION)

        tasks.parse_dsl(dsl_location=dsl_location,
                        resources_base_path=self.tmpdir,
                        resolver=resolver)

    def test_not_existing_plugin_import_resolver(self):

        dsl_location = os.path.join(
            '../.',
            'mock_blueprint',
            'blueprint_with_plugin_import.yaml')

        resolver = ResolverWithPlugins()
        self.assertRaises(InvalidPluginError, tasks.parse_dsl,
                          dsl_location=dsl_location,
                          resources_base_path=self.tmpdir,
                          resolver=resolver)


class TestBlueprintParseWithResolver(BaseServerTestCase):
    def test_success_with_catalog_source_substitution_mapping(self):
        expected_plan = models.Plan({
            constants.DESCRIPTION: "OUT",
            constants.METADATA: "OUT",
            constants.NODES: "",
            constants.RELATIONSHIPS: "",
            constants.WORKFLOWS: "",
            constants.POLICY_TYPES: "",
            constants.POLICY_TRIGGERS:
                "",
            constants.POLICIES:
                "",
            constants.GROUPS: "",
            constants.SCALING_GROUPS: "",
            constants.INPUTS: "",
            constants.OUTPUTS: "",
            constants.DEPLOYMENT_PLUGINS_TO_INSTALL:
                "",
            constants.WORKFLOW_PLUGINS_TO_INSTALL: "",
            constants.VERSION: "OUT",
            constants.SUBSTITUTION_MAPPING: "out"})

        blueprint_id = 'blueprint_with_substitution_mapping'
        self.put_blueprint('mock_blueprint',
                           'blueprint_with_substitution_mapping.yaml', blueprint_id)

        # The real testing
        dsl_location = os.path.join(
            '../.',
            'mock_blueprint',
            'blueprint_using_substitution_mapping.yaml')

        resolver = ResolverWithPlugins()

        plan = tasks.parse_dsl(dsl_location=dsl_location,
                               resources_base_path=self.tmpdir,
                               resolver=resolver)
        dsl_location = os.path.join(
            '../.',
            'mock_blueprint',
            'final_blueprint_with_substitution_mapping.yaml')

        expected_plan = tasks.parse_dsl(dsl_location=dsl_location,
                                        resources_base_path=self.tmpdir,
                                        resolver=resolver)

        self.assertEqual(plan, expected_plan)

    def test_missing_catalog_source_substitution_mapping(self):
        dsl_location = os.path.join(
            '../.',
            'mock_blueprint',
            'blueprint_using_substitution_mapping.yaml')

        resolver = ResolverWithPlugins()

        self.assertRaises(NotFoundError, tasks.parse_dsl,
                          dsl_location=dsl_location,
                          resources_base_path=self.tmpdir,
                          resolver=resolver)

    def test_local_import_with_substitution_mapping(self):
        dsl_location = os.path.join(
            '../.',
            'mock_blueprint',
            'blueprint_local_using_substitution_mapping.yaml')

        resolver = ResolverWithPlugins()

        plan = tasks.parse_dsl(dsl_location=dsl_location,
                               resources_base_path=self.tmpdir,
                               resolver=resolver)
