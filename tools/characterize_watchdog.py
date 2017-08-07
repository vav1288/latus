
import os
import time
import shutil
from functools import wraps

import threading

import watchdog.events
import watchdog.observers

start_time = time.time()
stop_watch = time.time()


def characterize(func):
    """
    decorator that adds characterization
    """
    @wraps(func)
    def characterized_function(self, *args, **kwargs):
        t = time.time()
        if not args[0].is_directory:
            print('%0.6f %0.6f : %s : %s, %s' % (t - start_time, t - stop_watch, func.__name__, args, kwargs))
        r = func(self, *args, **kwargs)
        # print('exit %0.6f : %s : %s' % (time.time() - start_time, func.__name__, args))
        return r
    return characterized_function


class CharacterizeWatchdog(watchdog.events.FileSystemEventHandler):
    def __init__(self, observed_dir):
        # there is no "super.__init__()"

        self.exit_event = threading.Event()

        self.observed_dir = observed_dir
        os.makedirs(self.observed_dir, exist_ok=True)

        self.observer = watchdog.observers.Observer()
        self.observer.schedule(self, self.observed_dir, recursive=True)

    def start(self):
        self.observer.start()

    def stop(self):
        self.observer.stop()

    @characterize
    def on_created(self, watchdog_event):
        pass

    @characterize
    def on_deleted(self, watchdog_event):
        pass

    @characterize
    def on_modified(self, watchdog_event):
        pass

    @characterize
    def on_moved(self, watchdog_event):
        pass


def write_file(path):
    with open(path, 'w') as f:
        f.write(path)


def pauser():
    global stop_watch
    time.sleep(1)
    print()
    stop_watch = time.time()


def main():
    temp_dir = 'temp'
    temp_path = os.path.join(temp_dir, 'temp.txt')
    temp_path2 = os.path.join(temp_dir, 'temp2.txt')
    try:
        os.remove(temp_path)
    except FileNotFoundError:
        pass
    wd = CharacterizeWatchdog(temp_dir)
    wd.start()

    print('simple write')
    write_file(temp_path)
    pauser()


    print('remove')
    os.remove(temp_path)
    pauser()

    print('write then move to existing')
    write_file(temp_path)
    write_file(temp_path2)
    shutil.move(temp_path, temp_path2)
    pauser()

    print('write then move to not existing - just shows write to temp2!')
    os.remove(temp_path2)
    time.sleep(1)
    write_file(temp_path)
    shutil.move(temp_path, temp_path2)
    pauser()

    print('write then move to not existing with wait')
    os.remove(temp_path2)
    write_file(temp_path)
    time.sleep(1)
    shutil.move(temp_path, temp_path2)
    pauser()

    print('modified')
    write_file(temp_path)
    time.sleep(1)
    write_file(temp_path)
    pauser()

    time.sleep(1)
    wd.stop()

if __name__ == '__main__':
    main()
