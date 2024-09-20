from celery import Task

from montrek.celery_app import PARALLEL_QUEUE_NAME, SEQUENTIAL_QUEUE_NAME


class QueueMixin:
    queue = None

    def apply_async(self, *args, **kwargs):
        kwargs.setdefault("queue", self.queue)
        return super().apply_async(*args, **kwargs)


class MontrekSequentialTaskBase(Task, QueueMixin):
    abstract = True
    queue = SEQUENTIAL_QUEUE_NAME


class MontrekParallelTaskBase(Task, QueueMixin):
    abstract = True
    queue = PARALLEL_QUEUE_NAME
