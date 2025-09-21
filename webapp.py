import asyncio
from dataclasses import dataclass
from nicegui import ui, background_tasks, app
from multiprocessing.managers import BaseManager
from queue import Queue, Empty
from collections import deque
import logging

from utils import DiamondPlace, decrypt_data, find_diamond, get_remain_harvest_count, get_place_name, get_resource_name
from manager import QueueManager


class DequeLogger(logging.Handler):

    def __init__(self,
                 mydeque: deque,
                 level: int | str = 0,
                 on_message=None) -> None:
        super().__init__(level)
        self.mydeque = mydeque
        self.on_message = on_message

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.mydeque.append(msg)
            if self.on_message:
                self.on_message(self)
        except Exception:
            self.handleError(record)


class Storage:
    INSTANCE = None


    def __init__(self) -> None:
        self.messages = deque(maxlen=100)
        self.log_handle = DequeLogger(self.messages, 0, self.on_message_append)
        self.example_diamond = DiamondPlace(
            5, {
                'resourceType': 'mysekai_material',
                'resourceId': 1,
                'positionX': -1,
                'positionZ': 18,
                'hp': 61,
                'seq': 99,
                'mysekaiSiteHarvestResourceDropStatus': 'before_drop',
                'quantity': 1,
            })

        self.last_found_diamonds: list[DiamondPlace] = []
        pass

    @classmethod
    def instance(cls):
        if cls.INSTANCE is None:
            cls.INSTANCE = cls()
        return cls.INSTANCE

    def on_message_append(self, sender):
        show_messages.refresh()

    def clear_messages(self):
        self.messages.clear()
        show_messages.refresh()

    def update_diamonds(self, diamonds: list[DiamondPlace]):
        self.last_found_diamonds.clear()
        self.last_found_diamonds.extend(diamonds)
        show_diamonds.refresh()


def try_find_diamond(data: bytes):
    logger = logging.getLogger()
    try:
        storage = Storage.instance()
        message = storage.messages
        decrypted_data = decrypt_data(data)
        harvest_count = get_remain_harvest_count(decrypted_data)
        logger.info('harvest_count: %s', harvest_count)
        ret = find_diamond(decrypted_data, 12)
        # ret = find_diamond(decrypted_data, 1)
        if ret is None:
            return
        if ret:
            logger.info('Find diamond')
            for d in ret:
                logger.info('%s', d)
        else:
            logger.info('Diamond not found')
        storage.update_diamonds(ret)
    except Exception as ex:
        logger.error('Exception: %s %s', type(ex), ex)


async def background_handle():
    logger = logging.getLogger()
    manager = QueueManager(address=('', 50000), authkey=b'abracadabra')
    manager.connect()
    queue: Queue = manager.get_queue()
    logger.info('connect to manager')
    while True:
        await asyncio.sleep(1)
        try:
            data = queue.get_nowait()
            logger.info('get data %s bytes', len(data))
            try_find_diamond(data)
        except Empty:
            pass


async def background():
    logger = logging.getLogger()
    while True:
        try:
            await background_handle()
        except Exception as e:
            logger.error('background connect fail: %s %s', type(e), e)
            await asyncio.sleep(10)
            pass


@ui.refreshable
def show_diamonds():
    storage = Storage.instance()
    diamonds = storage.last_found_diamonds
    with ui.list().props('bordered separator'):
        if not diamonds:
            with ui.item():
                with ui.item_section():
                    ui.item_label('No Diamond').props('header')

        for diamond in diamonds:
            drop = diamond.drop
            item_id = drop.get('resourceId', -1)
            item_name = get_resource_name(item_id)
            place_name = get_place_name(diamond.site_id)
            with ui.item():
                with ui.item_section():
                    ui.item_label(item_name)
                    ui.item_label(f'Place: {place_name}').props('caption')
                    ui.item_label(f'positionX: {drop.get('positionX')}').props('caption')
                    ui.item_label(f'positionZ: {drop.get('positionZ')}').props('caption')


@ui.refreshable
def show_messages():
    storage = Storage.instance()
    log = ui.log()
    for i in storage.messages:
        log.push(i)


@ui.page('/')
def main():
    show_diamonds()
    ui.button('clear', on_click=lambda: Storage.instance().clear_messages())
    show_messages()
    pass


app.on_startup(lambda: background_tasks.create(background()))

if __name__ in {"__main__", "__mp_main__"}:
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    formatter = logging.Formatter('%(asctime)s %(message)s',
                                  '%Y-%m-%d %H:%M:%S')
    handler = Storage.instance().log_handle
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)
    ui.run(reload=False)
