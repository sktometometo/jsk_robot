#!/usr/bin/env python3

import argparse
import logging
import os
import time
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def exist_interface(interface: str) -> bool:
    ret = os.system(f"nmcli d show {interface} > /dev/null 2>&1")
    return ret == 0


def restart_profile(profile: str) -> bool:
    os.system(f"nmcli c down {profile}")
    ret = os.system(f"nmcli c up {profile}")
    if ret == 0:
        logger.info(f"Restarted profile {profile}")
        return True
    else:
        logger.warning(f"Failed to restart profile {profile}. ret={ret}")
        return False


def get_interface_from_profile(profile: str) -> Optional[str]:
    """Get a network interface name from a network profile name.

    Args:
        profile (str): The network profile name.

    Returns:
        Optional[str]: The network interface name. If the profile is not found, return None.
    """
    ret = os.popen(f"nmcli connection show {profile} | grep GENERAL.DEVICES").read()
    if not ret or len(ret) == 0:
        return None
    return ret.replace("\n", "").split()[1]


def set_profile_metric(profile: Optional[str], metric: int) -> bool:
    if profile is None:
        return False
    device = get_interface_from_profile(profile)
    ret_nm = os.system(f"nmcli connection modify {profile} ipv4.route-metric {metric}")
    ret_ifmetric = os.system(f"ifmetric {device} {metric}")
    if ret_nm == 0 and ret_ifmetric == 0:
        logger.info(f"Set metric {metric} to profile {profile} and device {device}")
        return True
    else:
        logger.warning(
            f"Failed to set metric {metric} to profile {profile} and device {device}. ret={ret_nm}, {ret_ifmetric}"
        )
        return False


def get_profile_metric(profile: str) -> Optional[int]:
    interface = get_interface_from_profile(profile)
    if interface is None:
        return None
    ret = os.popen(
        f'nmcli d show {interface} | grep -i ip4.route | grep -i "dst = 0.0.0.0"'
    ).read()
    if not ret or len(ret) == 0:
        return None
    ret_split = ret.split()
    metric = ret_split[ret_split.index("mt") + 2]
    return int(metric)


def get_default_route_interface() -> Tuple[str, int]:
    """Get the default route interface and its metric."""
    ret = os.popen("ip route show default").read()
    if not ret:
        return "", 0
    ret_split = ret.split()
    metric = ret_split[ret_split.index("metric") + 1]
    device = ret_split[ret_split.index("dev") + 1]
    return device, int(metric)


def check_network_connection_with_interface(interface: str) -> bool:
    if interface is None:
        return False
    ret = os.system(f"ping -c 1 -W 1 1.1.1.1 -I {interface} > /dev/null 2>&1")
    return ret == 0


def check_network_connection_with_profile(profile: str) -> bool:
    interface = get_interface_from_profile(profile)
    if interface is None:
        return False
    return check_network_connection_with_interface(interface)


class NetworkConnectionManager:

    def __init__(
        self,
        wifi_profile: Optional[str],
        lte_profile: Optional[str],
        ethernet_profile: Optional[str],
    ):

        self.wifi_profile: Optional[str] = wifi_profile
        self.lte_profile: Optional[str] = lte_profile
        self.ethernet_profile: Optional[str] = ethernet_profile

        self.wifi_device: Optional[str] = (
            None if wifi_profile is None else get_interface_from_profile(wifi_profile)
        )
        self.lte_device: Optional[str] = (
            None if lte_profile is None else get_interface_from_profile(lte_profile)
        )
        self.ethernet_device: Optional[str] = (
            None
            if ethernet_profile is None
            else get_interface_from_profile(ethernet_profile)
        )

    def initialize_connection(
        self,
        initialize_ethernet: bool = True,
        initialize_wifi: bool = True,
        initialize_lte: bool = True,
    ):
        if initialize_lte and self.lte_profile is not None:
            if not self.connect_to_lte():
                logger.error("Failed to connect to LTE.")
                logger.error("Please check the LTE connection.")
                return

        if initialize_wifi and self.wifi_profile is not None:
            if not self.connect_to_wifi():
                logger.error("Failed to connect to Wi-Fi.")
                logger.error("Please check the Wi-Fi connection.")
                self.connect_to_lte()
                return

        if initialize_ethernet and self.ethernet_profile is not None:
            if not self.connect_to_ethernet():
                logger.error("Failed to connect to Ethernet.")
                logger.error("Please check the Ethernet connection.")
                self.connect_to_wifi()
                return

    def connect_to_ethernet(self) -> bool:
        if self.ethernet_profile is None:
            return False
        set_profile_metric(self.ethernet_profile, 90)
        set_profile_metric(self.wifi_profile, 600)
        set_profile_metric(self.lte_profile, 600)
        restart_profile(self.ethernet_profile)
        if check_network_connection_with_profile(self.ethernet_profile):
            return True
        else:
            return False

    def connect_to_wifi(self) -> bool:
        if self.wifi_profile is None:
            return False
        set_profile_metric(self.ethernet_profile, 600)
        set_profile_metric(self.wifi_profile, 90)
        set_profile_metric(self.lte_profile, 600)
        restart_profile(self.wifi_profile)
        if check_network_connection_with_profile(self.wifi_profile):
            return True
        else:
            return False

    def connect_to_lte(self) -> bool:
        if self.lte_profile is None:
            return False
        set_profile_metric(self.ethernet_profile, 600)
        set_profile_metric(self.wifi_profile, 600)
        set_profile_metric(self.lte_profile, 90)
        restart_profile(self.lte_profile)
        if check_network_connection_with_profile(self.lte_profile):
            return True
        else:
            return False

    def spin(
        self,
        interval: float = 1.0,
        interval_for_wifi_check: float = 10.0,
        interval_for_ethernet_check: float = 10.0,
    ):

        last_time_wifi_checked = time.time()
        last_time_ethernet_checked = time.time()
        while True:
            time.sleep(interval)
            default_route_interface, default_route_metric = (
                get_default_route_interface()
            )
            if not check_network_connection_with_interface(default_route_interface):
                logger.error(
                    f"Network connection with {default_route_interface} is down."
                )
                self.initialize_connection()
                last_time_wifi_checked = time.time()
                last_time_ethernet_checked = time.time()
                continue
            else:
                if time.time() > last_time_wifi_checked + interval_for_wifi_check and (
                    (
                        self.wifi_profile is not None
                        and self.wifi_device is not None
                        and exist_interface(self.wifi_device)
                        and default_route_interface != self.wifi_device
                    )
                    and (
                        self.ethernet_profile is None
                        or (
                            self.ethernet_profile is not None
                            and self.ethernet_device is not None
                            and exist_interface(self.ethernet_device)
                            and default_route_interface != self.ethernet_device
                        )
                    )
                ):
                    logger.error(
                        "Default connection is not Wi-Fi (nor ethernet). Retrying Wi-Fi connection..."
                    )
                    last_time_wifi_checked = time.time()
                    if not self.connect_to_wifi():
                        self.connect_to_lte()
                elif (
                    time.time()
                    > last_time_ethernet_checked + interval_for_ethernet_check
                    and self.ethernet_profile is not None
                    and self.ethernet_device is not None
                    and exist_interface(self.ethernet_device)
                    and default_route_interface != self.ethernet_device
                ):
                    logger.error(
                        "Default connection is not Ethernet. Retrying Ethernet connection..."
                    )
                    last_time_ethernet_checked = time.time()
                    if not self.connect_to_ethernet():
                        last_time_wifi_checked = time.time()
                        if not self.connect_to_wifi():
                            self.connect_to_lte()
                else:
                    logger.info("running. current interface: {}".format(default_route_interface))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--wifi-profile", type=str, default="")
    parser.add_argument("--lte-profile", type=str, default="")
    parser.add_argument("--ethernet-profile", type=str, default="")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    manager = NetworkConnectionManager(
        wifi_profile=args.wifi_profile if len(args.wifi_profile) > 0 else None,
        lte_profile=args.lte_profile if len(args.lte_profile) > 0 else None,
        ethernet_profile=(
            args.ethernet_profile if len(args.ethernet_profile) > 0 else None
        ),
    )
    manager.spin()
