from queue import Queue
from multiprocessing.managers import BaseManager


class Storage:
    INSTANCE = None

    def __init__(self) -> None:
        self.queue = Queue(10)

    @classmethod
    def get_instance(cls):
        if cls.INSTANCE is None:
            cls.INSTANCE = cls()
        return cls.INSTANCE


class QueueManager(BaseManager):
    get_queue: type[Queue]
    pass


QueueManager.register('get_queue',
                      callable=lambda: Storage.get_instance().queue)
