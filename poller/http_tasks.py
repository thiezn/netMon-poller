#!/usr/bin/env python3

import aiohttp
from poller import Task
from time import time


class GetPage(Task):
    """ Asynchronous class for common SSH queries """

    def __init__(self, url, *args, **kwargs):
        # TODO: Implement timeout to avoid hanging tasks
        super().__init__(*args, **kwargs)
        self.url = url

    def to_json(self):
        data = Task.to_json(self)
        data['url'] = self.url
        return data

    async def run(self):
        """ Run a single command on a remote device

        :param device: device to connect to
        :param cmd: the command to launch
        :param privilege: launch into enable mode (optional)
        :param port: use a custom port to connect to (optional)
        """

        result = {'start_timestamp': time()}

        with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.url) as response:
                    result['status_code'] = response.status
                    result['response'] = await response.text()
            except Exception as e:
                result['error'] = e

        result['end_timestamp'] = time()
        self.results.append(result)
        return result
