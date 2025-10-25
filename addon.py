import socket
import re
from multiprocessing.managers import BaseManager
from queue import Queue, Empty
import threading
import time
from mitmproxy import http
from utils import decrypt_data, find_diamond, get_remain_harvest_count
from manager import QueueManager

PATTERNS = [
    r'https://.*\.colorfulpalette\.org/.*/mysekai\?isForceAllReloadOnlyMysekai=(True|False)',
    r'https://.*\.colorfulpalette\.org/.*/mysekai/birthday-party/.*/delivery',
]

# /api/user/123123123123123/mysekai?isForceAllReloadOnlyMysekai=True
# /api/user/123123123123123/mysekai/birthday-party/2/delivery'


class SekaiDataSender:

    def __init__(self):
        self.queue: Queue = Queue(10)
        self.thread = threading.Thread(target=self.sender_loop, daemon=True)
        self.thread.start()

    def send_to_manager(self):
        manager = QueueManager(address=('', 50000), authkey=b'abracadabra')
        manager.connect()
        q: Queue = manager.get_queue()
        print('Connected to manager at 50000')
        while True:
            data = self.queue.get()
            q.put(data)

    def sender_loop(self):
        pending_data = None
        while True:
            manager = None
            q = None
            try:
                manager = QueueManager(address=('', 50000),
                                       authkey=b'abracadabra')
                manager.connect()
                q: Queue = manager.get_queue()
                print('Connected to manager at 50000')
                while True:
                    _ = q.qsize()

                    if pending_data is None:
                        try:
                            pending_data = self.queue.get(timeout=5)
                        except Empty:
                            pass

                    if pending_data is not None:
                        q.put(pending_data)
                        pending_data = None

            except Exception as ex:
                print('Sender Exception:', type(ex), ex)
                time.sleep(5)
            finally:
                del manager
                del q

    def send_data(self, data: bytes):
        self.queue.put(data)


class ShowSekai:

    def __init__(self):
        self.data_sender = SekaiDataSender()

    def try_find_diamond(self, data: bytes):
        try:
            decrypted_data = decrypt_data(data)
            harvest_count = get_remain_harvest_count(decrypted_data)
            print('harvest_count:', harvest_count)
            ret = find_diamond(decrypted_data, 12)
            if ret is None:
                return
            if ret:
                print('Find diamond')
                for d in ret:
                    print(d)
            else:
                print('Diamond not found')
        except Exception as ex:
            print('Exception:', ex)

    def response(self, flow: http.HTTPFlow):
        if 'colorfulpalette.org' in flow.request.pretty_url:
            print(flow.request.pretty_url)

            if (any(re.match(p, flow.request.pretty_url) for p in PATTERNS)
                    and flow.response):
                data = flow.response.content
                if data:
                    self.data_sender.send_data(data)
                    self.try_find_diamond(data)


addons = [ShowSekai()]
