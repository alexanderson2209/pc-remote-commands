from pywebostv.connection import WebOSClient
from pywebostv.controls import MediaControl, ApplicationControl, SourceControl
from pywebostv.model import InputSource


tv_ip = "192.168.68.119"


def open_tv_connection(client):
    store = {}
    client.connect()

    try:
        for status in client.register(store, timeout=10):
            if status == WebOSClient.PROMPTED:
                print("Please accept the connection on the TV!")
            elif status == WebOSClient.REGISTERED:
                print("Registration successful!")
    except Exception:
        print("Connection timed out")


client = WebOSClient(tv_ip, secure=True)

client.


open_tv_connection(client)
