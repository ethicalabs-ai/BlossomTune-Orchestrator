from collections import deque


class Log:
    def __init__(self, queue_maxlen: int = 1000):
        self.maxlen = queue_maxlen
        self.queue = deque(maxlen=queue_maxlen)

    @property
    def output(self) -> str:
        return "\n".join(self.queue)

    def __call__(self, msg: str):
        self.queue.append(msg)


log = Log()
