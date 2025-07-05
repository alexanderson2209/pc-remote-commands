from pywebostv.discovery import *
from pywebostv.connection import *
from pywebostv.controls import *
import os
import sys
import json
import time
import subprocess


def is_running_as_exe():
    return getattr(sys, "frozen", False)


def get_base_path():
    if is_running_as_exe():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_config_location():
    base_path = get_base_path()
    return os.path.join(base_path, "tv-config.json")


def your_custom_storage_is_empty():
    return not os.path.isfile(get_config_location())


def load_from_your_custom_storage():
    with open(get_config_location(), "r", encoding="utf-8") as f:
        return json.load(f)


def persist_to_your_custom_storage(store):
    with open(get_config_location(), "w", encoding="utf-8") as f:
        json.dump(store, f)


def switch_to_tv_profile(profile):
    username = os.getlogin()
    profile_path = (
        rf"C:\Users\{username}\AppData\Roaming\MonitorSwitcher\Profiles\{profile}.xml"
    )
    print(profile_path)
    exe_path = os.path.join(get_base_path(), "3rd-party", "MonitorSwitcher.exe")
    subprocess.run([exe_path, f"-load:{profile_path}"])


if your_custom_storage_is_empty():
    store = {}
else:
    store = load_from_your_custom_storage()

client = WebOSClient(
    "192.168.68.119", secure=True
)  # Use discover(secure=True) for newer models.
client.connect()
media = MediaControl(client)
app = ApplicationControl(client)
source_control = SourceControl(client)
for status in client.register(store):
    if status == WebOSClient.PROMPTED:
        print("Please accept the connect on the TV!")
    elif status == WebOSClient.REGISTERED:
        print("Registration successful!")


def switch_pc_to_tv():
    sources = source_control.list_sources()
    source_control.set_source(sources[3])
    time.sleep(4)
    switch_to_tv_profile("TV_Only")


def switch_pc_back():
    switch_to_tv_profile("2_Monitor")
    sources = source_control.list_sources()
    source_control.set_source(sources[1])


switch_pc_to_tv()
time.sleep(5)
switch_pc_back()

print(store)

persist_to_your_custom_storage(store)
