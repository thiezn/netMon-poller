.. _installation:

Installation
============

**warning** nothing is documented, figure it out or don't use it


netMon-poller
~~~~~~~~~~~~~~

The preferred installation method is through PyPi (aka pip install) but as of now
its not published. Will probably take a long time till it will be published

.. code-block:: bash

    pip install netmon-poller

If pip is unavailable for any reason you can also manually install from github:

.. code-block:: bash

    git clone https://github.com/thiezn/netMon-poller.git
    cd netMon-poller
    python3 setup.py test  # (optional) testing through py.test and/or tox
    python3 setup.py install
