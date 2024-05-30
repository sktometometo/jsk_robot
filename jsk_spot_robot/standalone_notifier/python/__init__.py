import logging

import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2, data_acquisition_plugin_service_pb2_grpc
from bosdyn.client.data_acquisition_plugin_service import (
    Capability,
    DataAcquisitionPluginService,
    DataAcquisitionStoreHelper,
)
from bosdyn.client.data_acquisition_store import DataAcquisitionStoreClient
from bosdyn.client.directory_registration import (
    DirectoryRegistrationClient,
    DirectoryRegistrationKeepAlive,
)
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.client.util import setup_logging
from google.protobuf import json_format

DIRECTORY_NAME = "data-acquisition-battery"
AUTHORITY = "data-acquisition-battery"
CAPABILITY = Capability(
    name="battery", description="Battery level", channel_name="battery"
)

_LOGGER = logging.getLogger("battery_plugin")
