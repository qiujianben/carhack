import time
from collections import defaultdict

class CAN(object):
    def __init__(self, simulate=False, logging=True):
        if not simulate:
            import pycanusb
            self.adapter = pycanusb.open(bitrate='500', callback=self.read)
        self.listeners = defaultdict(set)
        self.subscriptions = {}
        self.last_frame = {}

        if logging:
            import canlog
            fname = 'logs/can/canlog.%s.log' \
                % time.strftime('%Y-%m-%d.%H.%M.%S')
            self.log = canlog.CANLog(fname)
            self.subscribe(self.log)

    def simulate(self, frames):
        import threading

        if not frames:
            return

        def go():
            start_rt = time.time()
            start_st = frames[0].timestamp

            for frame in frames:
                s1 = frame.timestamp - start_st
                s2 = time.time() - start_rt
                s = s1 - s2
                if s > 0:
                    time.sleep(s)

                self.read(frame)

        thread = threading.Thread(target=go)
        thread.daemon = True
        thread.start()

    def read(self, frame):
        id = frame.id
        last = self.last_frame.get(id)
        self.last_frame[id] = frame
        duplicate = last and last.data == frame.data
        for k in [id, None]:
            for sub, suppress_duplicates in self.listeners[k]:
                if duplicate and suppress_duplicates:
                    continue
                sub(frame)

    # def interactive(self):
    #     import msvcrt
    #     while 1:
    #         c = getch()

    def subscribe(self, callback, ids=None, suppress_duplicates=False):
        if not ids:
            ids = [None]

        self.subscriptions[callback] = (ids, suppress_duplicates)

        for id in ids:
            self.listeners[id].add((callback, suppress_duplicates))

            if suppress_duplicates:
                last = self.last_frame.get(id)
                if last:
                    callback(last)

    def unsubscribe(self, callback):
        ids, suppress_duplicates = self.subscriptions.pop(callback)
        for id in ids:
            self.listeners[id].remove((callback, suppress_duplicates))


if __name__ == '__main__':
    can = CAN()

    try:
        while 1:
            time.sleep(2)
            s = can.adapter.status()
            print can.adapter.statusText(s)
            if s != 0:
                raise Exception

    except KeyboardInterrupt:
        print
        print 'Closing'
        print

    finally:
        can.log.close()
