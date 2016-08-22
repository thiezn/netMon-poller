# Network Monitoring Solution supporting SNMP, SSH, HTTP(s), DNS and TCP/IP polling written in Python3.5

This package consists of two main modules, the poller and the controller

The poller allows you to schedule SNMP, HTTP(S) and SSH related task using the Python3 asyncio framework. All tasks are run asynchronously (no threads or processes) from the server for optimal performance.  A REST API is used to schedule new tasks and return results

The controller will maintain the persisent storage of scheduled tasks and results. It can distribute tasks over multiple pollers if neccessary and uses the poller's REST API to interface. The controller provides a simple GUI interface for creating and maintaining tasks


## Poller - Whats working so far
- Common task manager handling scheduling of probes/tasks
  - in/out octets through SNMP
  - basic single command execution through SSH
  - HTTP(S) GET requests
  - PING probe (using subprocess to launch unix ping tool)
  - TRACE probe (using subprocess to launch unix traceroute tool)

- lightweight HTTP REST API for the task manager
  - retrieve all current scheduled tasks (GET http://localhost:8080/tasks)
  - Schedule a new SNMP/SSH/HTTP task (POST http://localhost:8080/tasks {'task': 'taskname', 'run_at': timestamp, etc..})

### TODO
- Associate unique task ID with scheduled tasks to be able to retrieve the results
- Retrieve results from completed tasks
- Add more SNMP queries
- Add more SSH queries
- Add POST/PUT/PATCH queries
- Add DNS task
- Add TCP/IP basic connect probes
- use SSH known hosts instead of user/pass


## Controller - Whats working so far
- Nothing really! :) there's only a simple bash script at the moment using curl that is able to register new tasks with the poller

### TODO
- Configuration loader to determine the available poller(s)
- Web frontend to create/manage tasks
- Storage strategy for scheduled task and task results
- everything else
