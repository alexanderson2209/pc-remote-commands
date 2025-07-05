# tv_remote.py

import os
import sys
import json
import time
import subprocess
from typing import List
from pywebostv.connection import WebOSClient
from pywebostv.controls import MediaControl, ApplicationControl, SourceControl
from pywebostv.model import InputSource


def is_running_as_exe():
    return getattr(sys, "frozen", False)


def get_base_path():
    if is_running_as_exe():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_config_location():
    return os.path.join(get_base_path(), "tv-config.json")


def get_3rd_party_folder():
    if is_running_as_exe():
        return os.path.join(sys._MEIPASS, "3rd-party")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "3rd-party")


def load_config():
    print(f"Config Location: {get_config_location()}")
    if os.path.isfile(get_config_location()):
        with open(get_config_location(), "r", encoding="utf-8") as f:
            return json.load(f)
    return {}  # Empty dict if config doesn't exist


def save_config(config):
    with open(get_config_location(), "w", encoding="utf-8") as f:
        json.dump(config, f)


def switch_to_tv_profile(profile_name):
    username = os.getlogin()
    profile_path = rf"C:\Users\{username}\AppData\Roaming\MonitorSwitcher\Profiles\{profile_name}.xml"
    exe_path = os.path.join(get_3rd_party_folder(), "MonitorSwitcher.exe")
    print(f"Switching profile: {profile_path}")
    subprocess.run([exe_path, f"-load:{profile_path}"])


class TVController:
    def __init__(
        self,
        tv_ip: str,
        pc_tv_profile: str,
        pc_desk_profile: str,
        pc_tv_input_label: str,
    ):
        self.tv_ip = tv_ip
        self.pc_tv_profile = pc_tv_profile
        self.pc_desk_profile = pc_desk_profile
        self.pc_tv_input_label = pc_tv_input_label
        self.store = load_config()

        self.client = WebOSClient(tv_ip, secure=True)
        self.open_tv_connection()
        self.save()

        # Initialize controls
        self.media = MediaControl(self.client)
        self.app = ApplicationControl(self.client)
        self.source_control = SourceControl(self.client)

        # Store sources
        self.sources: List[InputSource] = self.source_control.list_sources()
        self.current_source = self.get_current_source()

    def close_tv_connection(self):
        self.client.close_connection()

    def open_tv_connection(self):
        self.client.connect()

        for status in self.client.register(self.store):
            if status == WebOSClient.PROMPTED:
                print("Please accept the connection on the TV!")
            elif status == WebOSClient.REGISTERED:
                print("Registration successful!")

    def get_pc_source(self):
        return [x for x in self.sources if x["label"] == self.pc_tv_input_label][0]

    def get_current_source(self):
        current_app_id: str = self.app.get_current()
        return [x for x in self.sources if x.data["appId"] == current_app_id][0]

    def switch_pc_to_tv(self):
        # Storing current source so we can switch back later
        self.current_source = self.get_current_source()
        self.source_control.set_source(self.get_pc_source())
        time.sleep(4)
        switch_to_tv_profile(self.pc_tv_profile)

    def switch_pc_back(self):
        switch_to_tv_profile(self.pc_desk_profile)
        self.source_control.set_source(self.current_source)

    def save(self):
        save_config(self.store)


if __name__ == "__main__":
    from server import load_server_config

    server_config = load_server_config()

    tv = TVController(
        server_config["server"]["tv_ip"],
        server_config["server"]["pc_tv_profile"],
        server_config["server"]["pc_desk_profile"],
        server_config["server"]["pc_tv_input_label"],
    )
    tv.switch_pc_to_tv()
    time.sleep(5)
    tv.switch_pc_back()
    tv.save()
