#!/usr/bin/env python3

import asyncio
from time import time
import logging
import aiohttp
import json
from random import randint
logger = logging.getLogger(__name__)

__version = '0.0.1'


class Task:
    """ Class describing a Task for use in the TaskManager

    Args:
        run_at: when should the task run, use "now" for a immediate task
        recurrence_time: after how many seconds should the task re-occur
        recurrence_count: how often should the task re-occur
    """

    def __init__(self, *args, **kwargs):
        """ Define the task name, set the run at time and define
         recurrence if any

        kwargs:
            run_at: when should the task run, use "now" for a immediate task
            recurrence_time: after how many seconds should the task reoccur
            recurrence_count: how often should the task reoccur
        """
        self.results = []
        self.type = self.__class__.__name__

        run_at = kwargs.get('run_at', None)
        self._id = kwargs.get('_id', randint(1, 99999))
        recurrence_time = kwargs.get('recurrence_time', None)
        recurrence_count = kwargs.get('recurrence_count', None)

        if recurrence_count and not recurrence_time:
            raise ValueError('Can\'t create recurring task without recurrence_count')

        if not run_at:
            self.run_at = time()
        else:
            self.run_at = run_at

        self.name = self.__class__.__name__
        self.recurrence_time = recurrence_time
        self.recurrence_count = recurrence_count

    def to_json(self):
        data = {'run_at': self.run_at,
                '_id': self._id,
                'recurrence_time': self.recurrence_time,
                'recurrence_count': self.recurrence_count,
                'type': self.type}
        return data

    def __repr__(self):
        return ("Task ID {} type: {} run_at: {} recur_time: {} recur_count: {}"
                .format(self._id,
                        self.__class__.__name__,
                        self.run_at,
                        self.recurrence_time,
                        self.recurrence_count))

    @property
    def reschedule(self):
        """ Check if the Task has to reoccur again

        This should be run by the task_manager class each time
        it has run a Task that has the potential to be run again
        """

        if self.recurrence_time and not self.recurrence_count:
            # persistent reoccuring task
            self.run_at = time() + self.recurrence_time
            return True
        elif self.recurrence_time and self.recurrence_count > 1:
            # no persistent reoccuring task
            self.run_at = time() + self.recurrence_time
            self.recurrence_count -= 1
            return True
        else:
            # one off task
            return False

    async def run(self):
        """ Runs the specified task
        each task type has to overload this function """
        raise NotImplementedError


class TaskResult:
    """Results of a Task"""
    pass

    def to_json(self):
        pass

    @classmethod
    def from_json(self):
        pass


class TaskManager:
    """ Task Manager handling SNMP, SSH and HTTP tasks """

    def __init__(self, loop=None, async_debug=False):
        """ Initialise network handlers and task/result queues """

        # Initialise queues
        self.task_queue = asyncio.Queue()

        # Get asyncio event loop
        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()

        self.loop.set_debug(async_debug)

    async def register(self, controller, keepalive=120):
        """Register poller to controller and maintain keepalive

        :param controller: controller tuple of (ip, port)
        :param keepalive: The keepalive in seconds
        """
        url = "http://{}:{}/pollers/register".format(controller[0], controller[1])

        headers = {'content-type': 'application/json'}
        payload = {'name': 'dummy',
                   'ip': controller[0],
                   'port': controller[1]}

        with aiohttp.ClientSession() as session:
            logger.debug('Registering to controller {}'.format(controller))
            async with session.post(url, data=json.dumps(payload), headers=headers) as response:
                logger.debug('Controller response {}'.format(response.json()))

        while True:
            # Keepalive
            logger.debug('Sending keepalive to controller {}'.format(controller))
            await asyncio.sleep(keepalive)

    def shutdown(self):
        """ kills any pending tasks and shuts down the task manager """

        # TODO: Close off asyncio properly
        logging.info('Shutting down task manager')
        self.loop.stop()
        exit(0)

    def add(self, task):
        """ Add a task to the queue """
        # TODO: check if the task ID doesn't exist yet
        self.task_queue.put_nowait(task)

    def delete(self, task_id):
        """ delete a task from the queue """

        tasks = []
        while not self.task_queue.empty():
            task = self.task_queue.get_nowait()
            if task._id != task_id:
                tasks.append(task)

        for item in tasks:
            self.task_queue.put_nowait(item)

    async def process_tasks(self, load_interval=.5):
        """ Handle all scheduled tasks """
        while True:
            tasks_to_reschedule = []
            while not self.task_queue.empty():
                task = await self.task_queue.get()

                # Check if task is scheduled
                if time() >= task.run_at:
                    logger.debug('Running {}'.format(task))
                    asyncio.ensure_future(task.run())

                    if task.reschedule:
                        tasks_to_reschedule.append(task)
                else:
                    # Not scheduled to run yet, back of the queue
                    tasks_to_reschedule.append(task)

            for task_to_reschedule in tasks_to_reschedule:
                self.add(task_to_reschedule)

            await asyncio.sleep(load_interval)
            print('Task Queue: {}               '
                  .format(self.task_queue.qsize()), end='\r')
