#########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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

from flask import current_app
from mock import patch, MagicMock

from manager_rest.utils import traces
from manager_rest.utils import read_json_file, write_dict_to_json_file
from manager_rest.utils import plugin_installable_on_current_platform
from manager_rest.storage import models
from manager_rest.test import base_test
from manager_rest.test.attribute import attr


@attr(client_min_version=1, client_max_version=base_test.LATEST_API_VERSION)
class TestUtils(base_test.BaseServerTestCase):

    def test_read_write_json_file(self):
        test_dict = {'test': 1, 'dict': 2}
        tmp_file_path = os.path.join(self.tmpdir, 'tmp_dict.json')
        write_dict_to_json_file(tmp_file_path, test_dict)
        read_dict = read_json_file(tmp_file_path)
        self.assertEqual(test_dict, read_dict)

        test_dict = {'test': 3, 'new': 2}
        write_dict_to_json_file(tmp_file_path, test_dict)
        read_dict = read_json_file(tmp_file_path)
        self.assertEqual(3, read_dict['test'])
        self.assertEqual(test_dict, read_dict)

    @attr(client_min_version=2,
          client_max_version=base_test.LATEST_API_VERSION)
    def test_plugin_installable_on_current_platform(self):
        def create_plugin(supported_platform=None,
                          distribution=None,
                          distribution_release=None):
            # don't attempt to set read-only properties
            fields_to_skip = [
                'resource_availability',  # deprecated, proxies to .visibility
            ]
            mock_data = {k: 'stub' for k in models.Plugin.resource_fields
                         if k not in fields_to_skip}
            mock_data.pop('tenant_name')
            mock_data.pop('created_by')
            if supported_platform:
                mock_data['supported_platform'] = supported_platform
            if distribution:
                mock_data['distribution'] = distribution
            if distribution_release:
                mock_data['distribution_release'] = distribution_release
            return models.Plugin(**mock_data)

        plugin = create_plugin()
        self.assertFalse(plugin_installable_on_current_platform(plugin))

        plugin = create_plugin(supported_platform='any')
        self.assertTrue(plugin_installable_on_current_platform(plugin))

        platform = 'platform1'
        dist = 'dist1'
        rel = 'rel1'

        def mock_linux_dist(full_distribution_name):
            return dist, '', rel

        def mock_get_platform():
            return platform

        with patch('platform.linux_distribution', mock_linux_dist):
            with patch('wagon.get_platform', mock_get_platform):
                plugin = create_plugin(supported_platform=platform)
                self.assertFalse(
                    plugin_installable_on_current_platform(plugin))

                plugin = create_plugin(distribution=dist,
                                       distribution_release=rel)
                self.assertFalse(
                    plugin_installable_on_current_platform(plugin))

                plugin = create_plugin(supported_platform=platform,
                                       distribution=dist,
                                       distribution_release=rel)
                self.assertTrue(
                    plugin_installable_on_current_platform(plugin))

    def test_tracing_wrapper_does_nothing(self):
        # Dummy call to invoke the tracer initialization if enabled.
        self.app.get('/')

        foo = MagicMock(return_value='something')
        foo.__name__ = 'foo'
        app_patcher = patch('flask.current_app')
        curr_span_patcher = patch(
            'opentracing_instrumentation.request_context.get_current_span')
        span_ctx_patcher = patch(
            'opentracing_instrumentation.request_context.span_in_context')
        current_app = app_patcher.start()
        curr_span = curr_span_patcher.start()
        span_ctx_patcher.start()

        f = traces()(foo)
        current_app.tracer = False
        r = f('bar', k='v')
        self.assertEqual(r, 'something')
        foo.assert_called_once_with('bar', k='v')
        curr_span.assert_not_called()

        app_patcher.stop()
        curr_span_patcher.stop()
        span_ctx_patcher.stop()


class TestUtilsWithTracingTestCase(base_test.BaseServerTestCase):
    """Test the tracing wrapper when tracing is enabled.
    """
    _tracing_endpoint_ip = 'some_ip'

    def setUp(self):
        # old_traces = traces
        # manager_rest.utils.traces = dummy_traces
        super(TestUtilsWithTracingTestCase, self).setUp()
        # Dummy call to invoke the tracer initialization if enabled.
        self.app.get('/')
        # Makes sure `traces` gets called only when the tests starts.
        # manager_rest.utils.traces = old_traces

    def create_configuration(self):
        test_config = super(
            TestUtilsWithTracingTestCase, self).create_configuration()
        test_config.enable_tracing = True
        test_config.tracing_endpoint_ip = self._tracing_endpoint_ip
        return test_config

    def test_tracing_wrapper_works(self):
        foo = MagicMock(return_value='something')
        foo.__name__ = 'foo'
        curr_span_patcher = patch(
            'manager_rest.utils.get_current_span')
        curr_span = curr_span_patcher.start()
        span_ctx_patcher = patch(
            'manager_rest.utils.span_in_context')
        span_ctx = span_ctx_patcher.start()

        curr_span.return_value = curr_span
        current_app.tracer.start_span.reset_mock()

        f = traces('not_foo')(foo)
        r = f('bar', k='v')
        self.assertEqual(r, 'something')
        foo.assert_called_once_with('bar', k='v')
        curr_span.assert_called_once()
        current_app.tracer.start_span.assert_called_once_with(
            'not_foo', child_of=curr_span)
        span_ctx.assert_called_once()

        curr_span_patcher.stop()
        span_ctx_patcher.stop()

    def test_tracing_wrapper_works_no_name(self):
        foo = MagicMock(return_value='something')
        foo.__name__ = 'foo'
        curr_span_patcher = patch(
            'manager_rest.utils.get_current_span')
        curr_span = curr_span_patcher.start()
        span_ctx_patcher = patch(
            'manager_rest.utils.span_in_context')
        span_ctx = span_ctx_patcher.start()

        curr_span.return_value = curr_span
        current_app.tracer.start_span.reset_mock()

        f = traces()(foo)
        r = f('bar', k='v')
        self.assertEqual(r, 'something')
        foo.assert_called_once_with('bar', k='v')
        curr_span.assert_called_once()
        current_app.tracer.start_span.assert_called_once_with(
            'foo', child_of=curr_span)
        span_ctx.assert_called_once()

        curr_span_patcher.stop()
        span_ctx_patcher.stop()


def generate_progress_func(total_size, assert_equal,
                           assert_almost_equal, buffer_size=8192):
    """
    Generate a function that helps to predictably test upload/download progress
    :param total_size: Total size of the file to upload/download
    :param assert_equal: The unittest.TestCase assertEqual method
    :param assert_almost_equal: The unittest.TestCase assertAlmostEqual method
    :param buffer_size: Size of chunk
    :return: A function that receives 2 ints - number of bytes read so far,
    and the total size in bytes
    """
    # Wrap the integer in a list, to allow mutating it inside the inner func
    iteration = [0]
    max_iterations = total_size / buffer_size

    def print_progress(read, total):
        i = iteration[0]
        # tar.gz sizes are a bit inconsistent - tend to be a few bytes off
        assert_almost_equal(total, total_size, delta=5)

        expected_read_value = buffer_size * (i + 1)
        if i < max_iterations:
            assert_equal(read, expected_read_value)
        else:
            # On the last iteration, we face the same problem
            assert_almost_equal(read, total_size, delta=5)

        iteration[0] += 1

    return print_progress
