#!/usr/bin/env python3

import asyncssh
from poller import Task
from time import time


class SshRunSingleCommand(Task):
    """ Asynchronous class for common SSH queries """

    def __init__(self, device, cmd, username, password, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = device
        self.cmd = cmd
        self.username = username
        self.password = password
        self.known_hosts = None

    async def run(self):
        """ Run a single command on a remote device

        :param device: device to connect to
        :param cmd: the command to launch
        :param privilege: launch into enable mode (optional)
        :param port: use a custom port to connect to (optional)
        """

        result = {'start_timestamp': time()}

        with (await asyncssh.connect(self.device,
                                     username=self.username,
                                     password=self.password,
                                     known_hosts=self.known_hosts)) as session:

            stdin, stdout, stderr = await session.open_session(self.cmd)

            output = await stdout.read()
            result['output'] = output

            await stdout.channel.wait_closed()
            status = stdout.channel.get_exit_status()
            if status:
                result['error'] = status
            else:
                result['error'] = None

        result['end_timestamp'] = time()
        self.results.append(result)
