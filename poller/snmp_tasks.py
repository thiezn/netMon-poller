#!/usr/bin/env python3

from time import time
from poller import Task
from pysnmp.hlapi.asyncio import (SnmpEngine, CommunityData,
                                  UdpTransportTarget, ContextData,
                                  ObjectType, ObjectIdentity,
                                  getCmd, bulkCmd)
import asyncio


class Snmp:
    """ Asynchronous class for common SNMP queries """

    def __init__(self, community='public',
                 timeout=1, retries=0, port=161, lookup_mib=False):
        """ Initialise snmp engine """

        self.community = community
        self.snmp_engine = SnmpEngine()
        self.timeout = timeout
        self.retries = retries
        self.port = port
        self.lookup_mib = lookup_mib

    def shutdown(self):
        """ Shut down the SNMP engine """
        self.snmp_engine.transportDispatcher.closeDispatcher()

    async def _get(self, device, oid,
                   community=None,
                   timeout=None,
                   retries=None,
                   lookup_mib=None):
        """ Run async snmp GET request

        :param device: host to poll
        :param oid: SNMP OID to poll
        :param community: SNMP v2 community string
        :param timeout: SNMP GET timeout in sec (only use multiple of 0.5's)
        :param retries: amount of GET retries, 0 means a single poll
        :param lookupMib: can speed up things a little by turning off
        """
        if not community:
            community = self.community
        if not timeout:
            timeout = self.timeout
        if not retries:
            retries = self.retries
        if not lookup_mib:
            lookup_mib = self.lookup_mib

        (err_indication,
         err_status,
         err_index,
         var_binds) = await getCmd(self.snmp_engine,
                                   CommunityData(community),
                                   UdpTransportTarget((device, self.port),
                                                      timeout=timeout,
                                                      retries=retries),
                                   ContextData(),
                                   ObjectType(ObjectIdentity(oid)),
                                   lookupMib=lookup_mib)

        if err_indication:
            return {'error': str(err_indication)}
        else:
            for oid, value in var_binds:
                return {'value': value.prettyPrint()}

    async def _get_bulk(self, device, start_oid,
                        community=None,
                        timeout=None,
                        retries=None,
                        non_repeaters=0,
                        max_repetitions=25,
                        lookup_mib=None):
        """ Run async snmp GET BULK request

        :param device: host to poll
        :param oid: SNMP OID to poll
        :param community: SNMP v2 community string
        :param timeout: SNMP GET timeout in sec (only use multiple of 0.5's)
        :param retries: amount of GET retries, 0 means a single poll
        :param non_repeaters: amount of objects to retrieved with a get-next
        :param max_repetitions: amount of get-next to retrieve the remaining
        :param lookupMib: can speed up things a little by turning off
        """
        if not community:
            community = self.community
        if not timeout:
            timeout = self.timeout
        if not retries:
            retries = self.retries
        if not lookup_mib:
            lookup_mib = self.lookup_mib

        current_oid = start_oid
        result = {}

        while True:
            print(current_oid)
            (err_indication,
             err_status,
             err_index,
             var_binds) = await bulkCmd(self.snmp_engine,
                                        CommunityData(community),
                                        UdpTransportTarget((device, self.port),
                                                           timeout=timeout,
                                                           retries=retries),
                                        ContextData(),
                                        non_repeaters,
                                        max_repetitions,
                                        ObjectType(ObjectIdentity(current_oid)),
                                        lookupMib=lookup_mib)

            if err_indication:
                return {'error': str(err_indication)}
            else:
                for row in var_binds:
                    for oid, value in row:
                        if oid.prettyPrint().startswith(start_oid):
                            pretty_value = value.prettyPrint()
                            if pretty_value.startswith('0x'):
                                # Hack to convert long strings into
                                # ascii. pysnmp converts all strings
                                # longer than 7-bits to hex
                                pretty_value = str(value)
                            result[oid.prettyPrint()] = pretty_value
                        else:
                            # We've reached the last oid
                            return result
                current_oid = var_binds[-1]


class SystemInfoProbe(Task):
    """ Retrieves common system info """

    def __init__(self, device, snmp, *args, **kwargs):
        """ Making sure to pass on the scheduling variables to the
        main task.

        :param snmp: asyncio snmp class
        :param device: device to poll
        """

        super().__init__(*args, **kwargs)
        self.device = device
        self.snmp = snmp

    def to_json(self):
        data = Task.to_json(self)
        data['device'] = self.device
        data['if_index'] = self.if_index

        return data

    async def run(self):
        """ Gets common system information

        :param device: network device to query
        :param if_index: the interface if_index

        :return {'device' : <device name/ip>,
                 'if_index' <interface if_index>,
                 'ifHCInOctets' <in octets>,
                 'ifHCOutOctets': <interface out octets>,
                 'timestamp': <timestamp after poll>}
        """

        # OID definition
        sys_info_oid = '1.3.6.1.2.1.1'

        result = {'start_timestamp': time()}

        sys_info = await self.snmp._get_bulk(self.device, sys_info_oid)

        if 'error' in sys_info:
            result['error'] = sys_info['error']
        else:
            result['description'] = sys_info['1.3.6.1.2.1.1.1.0']
            result['object_id'] = sys_info['1.3.6.1.2.1.1.2.0']
            result['uptime'] = float(sys_info['1.3.6.1.2.1.1.3.0']) / 100
            result['contact'] = sys_info['1.3.6.1.2.1.1.4.0']
            result['name'] = sys_info['1.3.6.1.2.1.1.5.0']
            result['location'] = sys_info['1.3.6.1.2.1.1.6.0']
            result['services'] = sys_info['1.3.6.1.2.1.1.7.0']

        result['end_timestamp'] = time()

        self.results.append(result)


class InterfaceOctetsProbe(Task):
    """ Runs an ICMP probe to the provided destination """

    def __init__(self, device, if_index, snmp, *args, **kwargs):
        """ Making sure to pass on the scheduling variables to the
        main task.

        Args:
            snmp: asyncio snmp class
            device: device to poll
            if_index: The interface ifindex to poll ion/out octets from
        """

        super().__init__(*args, **kwargs)
        self.device = device
        self.if_index = if_index
        self.snmp = snmp

    def to_json(self):
        data = Task.to_json(self)
        data['device'] = self.device
        data['if_index'] = self.if_index

    async def run(self):
        """ Gets the in and out octets of a given interface

        :param device: network device to query
        :param if_index: the interface if_index

        :return {'device' : <device name/ip>,
                 'if_index' <interface if_index>,
                 'ifHCInOctets' <in octets>,
                 'ifHCOutOctets': <out octets>,
                 'end_timestamp': <timestamp after poll>}
        """
        # OID definition
        ifHCInOctets = '1.3.6.1.2.1.31.1.1.1.6.'
        ifHCOutOctets = '1.3.6.1.2.1.31.1.1.1.10.'

        result = {'start_timestamp': time()}

        # Incoming traffic
        in_octets = await self.snmp._get(self.device,
                                         ifHCInOctets + self.if_index)
        if 'value' in in_octets:
            result['ifHCInOctets'] = int(in_octets['value'])
        elif 'error' in in_octets:
            result['error'] = in_octets['error']
            result['ifHCInOctets'] = None
        else:
            result['ifHCInOctets'] = None

        # Outgoing traffic
        out_octets = await self.snmp._get(self.device,
                                          ifHCOutOctets + self.if_index)
        if 'value' in out_octets:
            result['ifHCOutOctets'] = int(out_octets['value'])
        elif 'error' in out_octets:
            result['error'] = in_octets['error']
            result['ifHCOutOctets'] = None
        else:
            result['ifHCOutOctets'] = None

        result['end_timestamp'] = time()
        self.results.append(result)


def main():
    snmp = Snmp(community='public')
    task = SystemInfoProbe('utecus01', snmp, _id=1)
    future = asyncio.ensure_future(task.run())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(future)
    snmp.shutdown()


if __name__ == '__main__':
    main()
