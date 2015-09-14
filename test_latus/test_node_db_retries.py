
import os
import multiprocessing
import time
import logging

import test_latus.paths
import test_latus.util

import latus.nodedb
import latus.logger


def get_node_db_retries_root():
    retries_root = os.path.join('c:', os.sep, 'temp')  # some place fast
    if not os.path.exists(retries_root):
        os.makedirs(retries_root)
    return retries_root


def writer(node_id, label):
    log_folder = os.path.join(get_node_db_retries_root(), 'log')
    test_latus.util.logger_init(log_folder)
    latus.logger.log.info('entering writer: %s' % node_id)
    db_writer = latus.nodedb.NodeDB(get_node_db_retries_root(), node_id, True)
    while True:
        db_writer.set_heartbeat()


def reader(node_id, label):
    log_folder = os.path.join(get_node_db_retries_root(), 'log')
    test_latus.util.logger_init(log_folder)
    latus.logger.log.info('entering reader: %s' % node_id)
    db_reader = latus.nodedb.NodeDB(get_node_db_retries_root(), node_id)
    no_retry = True
    while no_retry:
        # print(label, db_reader.get_retry_count(), db_reader.get_heartbeat())
        db_reader.get_heartbeat()
        if db_reader.get_retry_count() > 0:
            no_retry = False


def test_node_db_retries():
    log_folder = os.path.join(get_node_db_retries_root(), 'log')
    test_latus.util.logger_init(log_folder)
    node_id = 'abc'
    w = multiprocessing.Process(target=writer, args=(node_id, 'w', ))
    w.start()
    time.sleep(1)  # todo: make this some sort of pole
    read_processes = []
    for r in range(0, 20):
        read_processes.append(multiprocessing.Process(target=reader, args=(node_id, str(r), )))
    [r.start() for r in read_processes]
    latus.logger.log.info('all processes started')
    while all(r.is_alive() for r in read_processes):
        time.sleep(1)
    w.terminate()
    [r.terminate() for r in read_processes]