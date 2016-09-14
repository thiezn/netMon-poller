#!/usr/bin/env python3

from aiohttp import web
import asyncio
import logging
logger = logging.getLogger(__name__)

# Import tasks
from .snmp_tasks import InterfaceOctetsProbe, SystemInfoProbe
#from .ssh_tasks import SshRunSingleCommand
from .http_tasks import GetPage
from .ip_tasks import Ping, Trace


def queue_peek(queue):
    """ Peeks inside a (asyncio) Queue and returns a list
    of items. This is non-blocking and will not remove
    any items from the queue
    """
    # TODO: It only works on queue's with maxsize=0

    queue_list = []
    while not queue.empty():
        queue_list.append(queue.get_nowait())

    for item in queue_list:
        queue.put_nowait(item)

    return queue_list


class RestApi:

    def __init__(self, task_manager, ip='0.0.0.0', port='8080',
                 snmp_engine=None, ssh_user=None, ssh_pass=None, loop=None):
        """ Initialise Rest API

        :param task_manager: task_manager instance
        :param ip: ip address to listen on
        :param port: port to listen on
        """
        self.task_manager = task_manager
        self.ip = ip
        self.port = port
        self.snmp_engine = snmp_engine
        self.ssh_user = ssh_user
        self.ssh_pass = ssh_pass

        if loop:
            self.loop = loop
        elif task_manager.loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()

        self.app = web.Application(loop=self.loop)
        self.add_routes()

    def json_to_task(self, task):
        """ Converts a received json object to a Task """

        logger.debug('Parsing received task {}'.format(task))
        if task['type'] == 'InterfaceOctetsProbe':
            return InterfaceOctetsProbe(task['device'],
                                        task['if_index'],
                                        self.snmp_engine,
                                        _id=task['_id'],
                                        run_at=task['run_at'],
                                        recurrence_count=task.get('recurrence_count', None),
                                        recurrence_time=task.get('recurrence_time', None))
        elif task['type'] == 'SystemInfoProbe':
            return SystemInfoProbe(task['device'],
                                   self.snmp_engine,
                                   _id=task['_id'],
                                   run_at=task['run_at'],
                                   recurrence_count=task.get('recurrence_count', None),
                                   recurrence_time=task.get('recurrence_time', None))
        #elif task['type'] == 'SshRunSingleCommand':
        #    return SshRunSingleCommand(task['device'],
         #                              task['cmd'],
          #                             username=task.get('ssh_user', self.ssh_user),
           #                            password=task.get('ssh_pass', self.ssh_pass),
            #                           _id=task['_id'],
             #                          run_at=task['run_at'],
              #                         recurrence_count=task.get('recurrence_count', None),
               #                        recurrence_time=task.get('recurrence_time', None))
        elif task['type'] == 'GetPage':
            return GetPage(task['url'],
                           _id=task['_id'],
                           run_at=task['run_at'],
                           recurrence_count=task.get('recurrence_count', None),
                           recurrence_time=task.get('recurrence_time', None))
        elif task['type'] == 'Trace':
            return Trace(task['device'],
                         wait_time=task.get('wait_time', 1),
                         max_hops=task.get('max_hops', 20),
                         icmp=task.get('icmp', False),
                         _id=task['_id'],
                         run_at=task['run_at'],
                         recurrence_count=task.get('recurrence_count', None),
                         recurrence_time=task.get('recurrence_time', None))
        elif task['type'] == 'Ping':
            return Ping(task['device'],
                        count=task.get('count', 9),
                        preload=task.get('preload', 3),
                        timeout=task.get('timeout', 1),
                        _id=task['_id'],
                        run_at=task['run_at'],
                        recurrence_count=task.get('recurrence_count', None),
                        recurrence_time=task.get('recurrence_time', None))
        else:
            return None

    def task_to_json(self, task):
        """ Converts a task to a JSON object """

        task_type = task.__class__.__name__

        json_task = {'run_at': task.run_at,
                     'recurrence_count': task.recurrence_count,
                     'recurrence_time': task.recurrence_time,
                     '_id': task._id,
                     'type': task_type,
                     'results': task.results}

        if task_type == 'InterfaceOctetsProbe':
            json_task['device'] = task.device
            json_task['if_index'] = task.if_index
        elif task_type == 'SystemInfoProbe':
            json_task['device'] = task.device
       # elif task_type == 'SshRunSingleCommand':
        #    json_task['device'] = task.device
         #   json_task['cmd'] = task.cmd
        elif task_type == 'GetPage':
            json_task['url'] = task.url
        elif task_type == 'Trace':
            json_task['device'] = task.device
            json_task['wait_time'] = task.wait_time
            json_task['max_hops'] = task.max_hops
            json_task['icmp'] = task.icmp
        elif task_type == 'Ping':
            json_task['device'] = task.device
            json_task['count'] = task.count
            json_task['preload'] = task.preload
            json_task['timeout'] = task.timeout
        else:
            return None

        return json_task

    def start(self):
        web.run_app(self.app, host=self.ip, port=self.port)

    def add_routes(self):
        """ Registers all the routes """
        logger.debug('Adding route GET /results')
        self.app.router.add_route('GET', '/results', self.get_results)
        logger.debug('Adding route GET /tasks')
        self.app.router.add_route('GET', '/tasks', self.get_tasks)
        logger.debug('Adding route POST /tasks')
        self.app.router.add_route('POST', '/tasks', self.post_tasks)
        logger.debug('Adding route DELETE /tasks')
        self.app.router.add_route('DELETE', '/tasks', self.delete_task)
        logger.debug('Adding route GET /tasks/{task_id}')
        self.app.router.add_route('GET', '/tasks/{task_id}', self.get_task)

    async def get_task(self, request):
        """ Returns a single given task """

        task_id = request.match_info['task_id']

        tasks = queue_peek(self.task_manager.task_queue)
        for task in tasks:
            if str(task._id) == str(task_id):
                return web.json_response(self.task_to_json(task))

        return web.json_response({'error': 'Task {} not found'
                                           .format(task_id)})

    async def post_tasks(self, request):
        """ Schedule a new task on the poller

        if the task['run_instant'] is True it will return the result
        as soon as possible """

        data = await request.json()
        task = self.json_to_task(data)
        if task:
            logger.info('Adding {} to task_manager'.format(task))
            self.task_manager.add(task)

            # TODO: Fix the result fetching for a task
            if 'run_instant' in data and data['run_instant']:
                while True:
                    item = 'not working dummy!'
                    # queue = queue_peek(self.task_manager.result_queue)
                    # for item in queue:
                    #    if data['_id'] == item['_id']:
                    return web.json_response(item, status=200)
                    # await asyncio.sleep(.5)
            else:
                return web.Response(status=204)
        else:
            return web.json_response({'error': 'task type not found'},
                                     status=501)

    async def get_tasks(self, request):
        """ Returns all current scheduled tasks """

        tasks = queue_peek(self.task_manager.task_queue)
        json_tasks = []
        for task in tasks:
            json_tasks.append(self.task_to_json(task))

        return web.json_response(json_tasks)

    async def delete_task(self, request):
        """ Returns all current scheduled tasks """

        data = await request.json()
        if 'task_id' in data:
            self.task_manager.delete(data['task_id'])
            return web.Response(status=204)
        else:
            return web.json_response({'error': 'Expecting {"task_id": "id"}'},
                                     status=400)

    async def get_results(self, request):
        """ This returns all available results """

        results = []

        tasks = queue_peek(self.task_manager.task_queue)
        for task in tasks:
            results.append({task._id: task.results})

        # response = queue_peek(self.task_manager.result_queue)
        return web.json_response(results)
