#!/usr/bin/env python3

import logging
import asyncio
from poller import TaskManager, RestApi
from poller.snmp_tasks import Snmp
from poller.utils import load_config_file


def main():

    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='log.main',
                        level=logging.DEBUG,
                        filemode='w',
                        format='%(asctime)s %(levelname)s %(message)s')

    logger.info('Loading config.json')
    ssh_user, ssh_pass, snmp_community = load_config_file()
    logger.info('Loading task_manager...')
    task_manager = TaskManager(async_debug=False)
    logger.info('Loading SNMP handler')
    snmp_engine = Snmp(community=snmp_community)

    # If you want to add tasks before starting as a test place them here
    # task_manager.add(Ping('10.243.48.5', run_at=time(), recurrence_time=5))
    # task_manager.add(Trace('10.243.48.5', run_at=time(), recurrence_time=3))

    logger.info('Registering task manager to asyncio loop')
    asyncio.ensure_future(task_manager.process_tasks())

    logger.info('Loading REST API...')
    rest_api = RestApi(task_manager,
                       ip='127.0.0.1', port='9090',
                       snmp_engine=snmp_engine,
                       ssh_user=ssh_user, ssh_pass=ssh_pass)

    try:
        # This will start the asyncio loop so the
        # task manager futures will run as well
        rest_api.start()
    except KeyboardInterrupt:
        task_manager.shutdown()


if __name__ == '__main__':
    main()
