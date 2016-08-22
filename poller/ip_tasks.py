#!/usr/bin/env python3

from asyncio import create_subprocess_exec, subprocess
from poller import Task
from time import time
import ipaddress


class Trace(Task):
    """ Asynchronous class for traceroute probes """

    def __init__(self, device, wait_time=1, max_hops=20, icmp=False,
                 *args, **kwargs):
        """ Init Task """
        super().__init__(*args, **kwargs)
        self.device = device
        self.wait_time = str(wait_time)
        self.max_hops = str(max_hops)
        self.icmp = icmp

    async def run(self):
        """ Runs a traceroute using the OS traceroute function """

        result = {'hops': [],
                  'start_timestamp': time()}

        if self.icmp:
            trace = await create_subprocess_exec("traceroute",
                                                 "-n",
                                                 "-I",
                                                 "-w" + self.wait_time,
                                                 "-m" + self.max_hops,
                                                 "-q 1",
                                                 self.device,
                                                 stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE)
        else:
            trace = await create_subprocess_exec("traceroute",
                                                 "-n",
                                                 "-w" + self.wait_time,
                                                 "-m" + self.max_hops,
                                                 "-q 1",
                                                 self.device,
                                                 stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE)

        stdout = await trace.stdout.read()
        stderr = await trace.stderr.read()

        if stderr:
            result['error'] = stderr

        lines = stdout.splitlines()
        # remove first line "traceroute to..."
        del lines[0]

        for line in lines:
            line = line.decode('utf-8')
            ip_address = self.extract_ip_from_line(line)
            rtt = self.extract_rtt_from_line(line)
            if(ip_address):
                result['hops'].append({'ip_address': ip_address,
                                       'rtt': rtt})
            elif '*' in line:
                result['hops'].append({'ip_address': '*',
                                       'rtt': '*'})

        result['end_timestamp'] = time()
        self.results.append(result)

    def extract_rtt_from_line(self, line):
        """ Fetch the first occurance of the round-trip time of
        a traceroute output """

        if line:
            rtt = line.split(' ms')[0].split()[-1]
            return rtt
        else:
            return None

    def extract_ip_from_line(self, line):
        """ Check a string line to see if there's an valid IP address """

        ip = line.split()[1]
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            if ip != "*":
                return None
        return ip


class Ping(Task):
    """ Asynchronous class for Ping probes """

    def __init__(self, device, count=9, preload=3, timeout=1,
                 *args, **kwargs):
        """ Init task """
        super().__init__(*args, **kwargs)
        self.device = device
        self.count = str(count)
        self.preload = str(preload)
        self.timeout = str(timeout)

    async def run(self):
        """ Runs a ping using the OS ping function

        Returns:
            True: Returns true if the probe was succesful
        """

        result = {'start_timestamp': time()}

        ping = await create_subprocess_exec("ping",
                                            self.device,
                                            "-c " + self.count,
                                            "-l " + self.preload,
                                            "-W " + self.timeout,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
        stdout = await ping.stdout.read()
        stderr = await ping.stderr.read()

        if stderr:
            result['error'] = stderr.decode('utf-8').strip()
        else:
            lines = stdout.splitlines()
            second_last_line = lines[len(lines)-2].decode('utf-8').split()
            last_line = lines[len(lines)-1].decode('utf-8')
            if not last_line:
                # if the last line is empty
                # none of the packets arrived
                result['error'] = 'Host unreachable'
                result['packets_sent'] = second_last_line[0]
                result['packets_recv'] = second_last_line[3]
            else:
                last_line = last_line.split()[3].split('/')
                result['min'] = last_line[0]
                result['avg'] = last_line[1]
                result['max'] = last_line[2]
                result['mdev'] = last_line[3]
                result['packets_sent'] = second_last_line[0]
                result['packets_recv'] = second_last_line[3]

        result['end_timestamp'] = time()
        self.results.append(result)
        return result
