
import os
import multiprocessing
import time

from test_latus.tstutil import get_data_root, logger_init

from latus import nodedb
import latus.logger


def get_node_db_retries_root():
    retries_root = os.path.join(get_data_root(), 'temp')
    if not os.path.exists(retries_root):
        os.makedirs(retries_root)
    return retries_root


def writer(node_id, label):
    log_folder = os.path.join(get_node_db_retries_root(), 'log')
    logger_init(log_folder)
    latus.logger.log.info('entering writer: %s' % node_id)
    db_writer = nodedb.NodeDB(get_node_db_retries_root(), node_id, True)
    while True:
        db_writer.set_heartbeat()


def reader(node_id, label):
    log_folder = os.path.join(get_node_db_retries_root(), 'log')
    logger_init(log_folder)
    latus.logger.log.info('entering reader: %s' % node_id)
    db_reader = nodedb.NodeDB(get_node_db_retries_root(), node_id)
    # I'd rather not have a count down, but we're not guaranteed we'll ever get a retry
    count_down = 1000
    while count_down > 0:
        # print(label, db_reader.get_retry_count(), db_reader.get_heartbeat())
        db_reader.get_heartbeat()
        if db_reader.get_retry_count() > 0:
            count_down = 0
        count_down -= 1


def test_node_db_retries(session_setup, module_setup):
    log_folder = os.path.join(get_node_db_retries_root(), 'log')
    logger_init(log_folder)
    node_id = 'abc'
    w = multiprocessing.Process(target=writer, args=(node_id, 'w', ))
    w.start()
    time.sleep(1)  # todo: make this some sort of poll
    read_processes = []
    for r in range(0, 20):
        read_processes.append(multiprocessing.Process(target=reader, args=(node_id, str(r), )))
    [r.start() for r in read_processes]
    latus.logger.log.info('all processes started')
    while all(r.is_alive() for r in read_processes):
        time.sleep(1)
    w.terminate()
    [r.terminate() for r in read_processes]
