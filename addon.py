import socket
import re
from multiprocessing.managers import BaseManager
from queue import Queue
from mitmproxy import http
from utils import decrypt_data, find_diamond, get_remain_harvest_count
from manager import QueueManager

PATTERN = r'https://.*\.colorfulpalette\.org/.*/mysekai\?isForceAllReloadOnlyMysekai=(True|False)'
# /api/user/123123123123123/mysekai?isForceAllReloadOnlyMysekai=True


class ShowSekai:

    def __init__(self):
        self.manager = QueueManager(address=('', 50000),
                                    authkey=b'abracadabra')
        self.manager.start()

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

            if re.match(PATTERN, flow.request.pretty_url) and flow.response:
                data = flow.response.content
                if data:
                    q = self.manager.get_queue()
                    q.put(data)
                    # self.udp.sendto(data, self.target)
                    self.try_find_diamond(data)


addons = [ShowSekai()]
