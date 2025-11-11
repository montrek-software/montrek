Montrek Tasks and Celery

## Task Classes

Montrek provides a custom task class, `MontrekTask`, which inherits from Celery's `Task` class. This class is designed to handle tasks specific to the Montrek framework.

### MontrekTask

The `MontrekTask` class is the base class for all tasks in Montrek. It provides a basic implementation of a task and can be extended to create custom tasks.

```python
from tasks.montrek_task import MontrekTask

class MyTask(MontrekTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        # Task implementation here
        pass
```

## Celery Configuration and Usage

To use Celery with Montrek, you need to configure it in your Django project. Here's an example of how to do it:

### settings.py

```python
CELERY_BROKER_URL = 'amqp://localhost'
CELERY_RESULT_BACKEND = 'amqp://localhost'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
```

### celery.py

```python
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

To run a task, you can use the `delay` method:

```python
my_task = MyTask()
my_task.delay()
```

## Asynchronous Task Execution

Montrek provides a way to execute tasks asynchronously using Celery. To do this, you need to create a task instance and call the `delay` method:

```python
my_task = MyTask()
my_task.delay()
```

This will send a message to the Celery broker, which will then execute the task in the background.

### Example

Here's an example of how to create a task that sends an email:

```python
from tasks.montrek_task import MontrekTask
from django.core.mail import send_mail

class SendEmailTask(MontrekTask):
    def __init__(self, subject, message, from_email, to_email):
        self.subject = subject
        self.message = message
        self.from_email = from_email
        self.to_email = to_email

    def run(self):
        send_mail(self.subject, self.message, self.from_email, [self.to_email])
```

To run this task, you can use the `delay` method:

```python
send_email_task = SendEmailTask('Hello', 'This is a test email', 'from@example.com', 'to@example.com')
send_email_task.delay()
```

This will send an email in the background using Celery.

## Summary

In this section, we covered the basics of Montrek tasks and Celery. We learned how to create custom tasks, configure Celery, and execute tasks asynchronously.

## Next Steps

* Learn more about Celery and its features
* Explore the Montrek framework and its capabilities
* Create your own custom tasks and integrate them with your Django project

By following these steps, you can unlock the full potential of Montrek and Celery, and take your Django project to the next level.
