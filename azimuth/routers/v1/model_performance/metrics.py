# Copyright ServiceNow, Inc. 2021 – 2022
# This source code is licensed under the Apache 2.0 license found in the LICENSE file
# in the root directory of this source tree.
from typing import List

from fastapi import APIRouter, Depends

from azimuth.app import get_dataset_split_manager, get_task_manager
from azimuth.dataset_split_manager import DatasetSplitManager
from azimuth.modules.model_performance.metrics import MetricsModule
from azimuth.task_manager import TaskManager
from azimuth.types.general.dataset import DatasetSplitName
from azimuth.types.general.module_options import ModuleOptions, NamedDatasetFilters
from azimuth.types.general.modules import SupportedModule
from azimuth.types.model_performance import (
    MetricsAPIResponse,
    MetricsModuleResponse,
    MetricsPerFilterAPIResponse,
    MetricsPerFilterModuleResponse,
    MetricsPerFilterValue,
)
from azimuth.utils.routers import (
    build_named_dataset_filters,
    get_standard_task_result,
    require_pipeline_index,
)

router = APIRouter()

TAGS = ["Metrics v1"]


@router.get(
    "",
    summary="Get metrics.",
    description="Get metrics (ECE, outcome count, precision and so on).",
    tags=TAGS,
    response_model=MetricsAPIResponse,
)
def get_metrics(
    dataset_split_name: DatasetSplitName,
    named_filters: NamedDatasetFilters = Depends(build_named_dataset_filters),
    task_manager: TaskManager = Depends(get_task_manager),
    dataset_split_manager: DatasetSplitManager = Depends(get_dataset_split_manager),
    pipeline_index: int = Depends(require_pipeline_index),
) -> MetricsAPIResponse:
    mod_options = ModuleOptions(
        filters=named_filters.to_dataset_filters(dataset_split_manager.get_class_names()),
        pipeline_index=pipeline_index,
    )

    module_response: List[MetricsModuleResponse] = get_standard_task_result(
        SupportedModule.Metrics,
        dataset_split_name,
        task_manager,
        mod_options=mod_options,
        last_update=dataset_split_manager.last_update,
    )

    api_response = MetricsModule.module_to_api_response(module_response)

    return api_response[0]


@router.get(
    "/per_filter",
    summary="Get metrics for each filter.",
    description="Get metrics for each filter based on the current filtering.",
    tags=TAGS,
    response_model=MetricsPerFilterAPIResponse,
)
def get_metrics_per_filter(
    dataset_split_name: DatasetSplitName,
    task_manager: TaskManager = Depends(get_task_manager),
    dataset_split_manager: DatasetSplitManager = Depends(get_dataset_split_manager),
    pipeline_index: int = Depends(require_pipeline_index),
) -> MetricsPerFilterAPIResponse:
    mod_options = ModuleOptions(pipeline_index=pipeline_index)
    metrics_per_filter_result: MetricsPerFilterModuleResponse = get_standard_task_result(
        SupportedModule.MetricsPerFilter,
        dataset_split_name,
        task_manager,
        mod_options=mod_options,
        last_update=dataset_split_manager.last_update,
    )[0]

    metrics_result: MetricsPerFilterModuleResponse = get_standard_task_result(
        SupportedModule.Metrics,
        dataset_split_name,
        task_manager,
        mod_options=mod_options,
        last_update=dataset_split_manager.last_update,
    )[0]

    api_result = MetricsPerFilterAPIResponse(
        **metrics_per_filter_result.dict(),
        metrics_overall=[MetricsPerFilterValue(**metrics_result.dict(), filter_value="overall")]
    )

    return api_result
