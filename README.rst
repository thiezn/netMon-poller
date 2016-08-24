netMon-controller: Distributed Network Monitoring
=================================================

|Build Status| |Coverage Status| |Documentation Status|

Detailed documentation at
`netmon-poller.readthedocs.org <https://netmon-poller.readthedocs.org/>`__

netMon is a distributed network monitoring solution written in python. The netMon poller is a
single poller instance that can perform various probes on the network. It provides a RESTful
interface for easy interaction.

These pollers can be controlled directly by the API but the best way is to use the netMon-controller.
The controller provides a central place to monitor all running probes and is able to correlate data.

Installation
------------

.. code:: bash

    git clone https://github.com/thiezn/netMon-poller.git
    cd netMon-poller
    sudo pip3 install -r requirements.txt
    ./run-poller.py

Quickstart
----------

**Server**

.. code:: bash

    ./run_poller.py


External Dependencies
---------------------

-  aiohttp
-  asyncssh
-  some other stuff

Testing
-------

- Tested against Ubuntu 14.04 LTS using `travis-ci <https://travis-ci.org/>`__
- Test coverage reporting through `coveralls.io <https://coveralls.io/>`__
- Tested against the following Python versions:
    * 3.5
    * 3.5-dev 
    * nightly

.. |Build Status| image:: https://travis-ci.org/thiezn/netMon-poller.svg?branch=master
   :target: https://travis-ci.org/thiezn/netMon-poller
.. |Coverage Status| image:: https://coveralls.io/repos/github/thiezn/netMon-poller/badge.svg?branch=master
   :target: https://coveralls.io/github/thiezn/netMon-poller?branch=master
.. |Documentation Status| image:: https://readthedocs.org/projects/netMon/badge/?version=latest
   :target: http://netmon.readthedocs.io/en/latest/?badge=latest
