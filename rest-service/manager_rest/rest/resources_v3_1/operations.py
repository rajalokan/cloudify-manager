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

from flask_restful.reqparse import Argument
from manager_rest.rest.rest_utils import (
    get_args_and_verify_arguments,
    get_json_and_verify_params,
)
from manager_rest.rest.rest_decorators import (
    exceptions_handled,
    marshal_with,
)
from manager_rest.storage import (
    get_storage_manager,
    models
)
from manager_rest.resource_manager import get_resource_manager
from manager_rest.security import SecuredResource


class Operations(SecuredResource):
    @exceptions_handled
    @marshal_with(models.Operation)
    def get(self, _include=None, **kwargs):
        args = get_args_and_verify_arguments(
            [Argument('execution_id', type=unicode, required=True)]
        )
        execution_id = args.get('execution_id')
        return get_storage_manager().list(
            models.Operation,
            filters={'_execution_fk': execution_id}
        ).items


class OperationsId(SecuredResource):
    @exceptions_handled
    @marshal_with(models.Operation)
    def put(self, operation_id, **kwargs):
        params = get_json_and_verify_params(
            [Argument('name', type=str, required=True),
             Argument('execution_id', type=str, required=True)]
        )
        operation = get_resource_manager().create_operation(
            operation_id,
            name=params['name'],
            execution_id=params['execution_id'],
        )
        return operation, 201

    @exceptions_handled
    @marshal_with(models.Operation)
    def patch(self, operation_id, **kwargs):
        request_dict = get_json_and_verify_params(
            {'state': {'type': str}}
        )
        sm = get_storage_manager()
        instance = sm.get(models.Operation, operation_id, locking=True)
        instance.state = request_dict.get('state', instance.state)
        return sm.update(instance)
