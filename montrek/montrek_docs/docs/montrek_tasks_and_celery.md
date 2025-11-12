Montrek Tasks and Celery

## Overview

Montrek provides a robust task management system built on top of Celery, a distributed task queue. This allows for asynchronous execution of tasks, enabling efficient and scalable data processing.

## Task Classes

### MontrekTask

The `MontrekTask` class is the base class for all tasks in Montrek. It provides a standardized interface for defining tasks and handling task execution.

```python
from celery import Task
from baseclasses.tasks import MontrekTask

class MyTask(MontrekTask):
    def run(self, *args, **kwargs):
        # Task execution logic here
        pass
```

## Celery Configuration and Usage

To use Celery with Montrek, you need to configure the Celery broker and backend. This can be done in the `settings.py` file:

```python
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

Once configured, you can use the `celery` command to start the worker:

```bash
celery -A myapp worker -l info
```

## Asynchronous Task Execution

To execute a task asynchronously, you can use the `apply_async` method:

```python
from myapp.tasks import MyTask

task = MyTask()
task.apply_async(args=['arg1', 'arg2'], kwargs={'key': 'value'})
```

This will schedule the task for execution by the Celery worker.

## Summary

Montrek's task management system, built on top of Celery, provides a robust and scalable way to execute tasks asynchronously. By defining tasks using the `MontrekTask` class and configuring Celery, you can take advantage of this powerful feature to build efficient and scalable data-driven applications.
