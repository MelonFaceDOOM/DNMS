from flask import current_app, url_for, jsonify
import redis
import time

def is_redis_available():
    r = redis.from_url(current_app.config['CELERY_BROKER_URL'])
    try:
        r.ping()
        return True
    except redis.exceptions.ConnectionError:
        return False

class Scraper:
    def __init__(self, name, task_func):
        self.name = name
        self.task_id = None
        self.task_func = task_func

    def assign_worker(self):
        # TODO: replace this with a more definite check for whether or not a worker is available
        task = self.task_func.apply_async()
        retries = 0
        while True:
            time.sleep(0.2)
            try:
                task.info.get('current', 0)  # This succeeds if a worker picked up the task, and fails otherwise
                self.task_id = task.id  # task_id is only set if a worker is confirmed to have picked up the task
                return self.task_id
            except AttributeError:
                retries += 1
            if retries > 15:
                return None

    def start_task(self):
        """starts the task and returns basic info"""

        if not is_redis_available():
            return jsonify({}), 500, {'message-body': "Could not make connection to Redis"}

        if self.task_id:
            if self.status()['state'] != "PENDING" and self.status()['state'] != "PROGRESS":
                self.task_id = None  # remove id if task is stale
        if self.task_id == None:
            if self.assign_worker():
                return jsonify({}), 202, {'Location': url_for('scraping.check_status', scraper_name=self.name)}
            else:
                return jsonify({}), 500, {'message-body': "Redis is running, but a worker could not be assigned "
                                                          "to the task"}

    def is_running(self):
        # TODO: add a harder check on whether or not this is running
        if not self.task_id:
            return False

        # if the task pending or in progress, leave it and indicate that it is running
        # otherwise, the task is dead, so the task_id should be deleted
        if self.status()['state'] == "PENDING" or self.status()['state'] == "PROGRESS":
            return True
        else:
            self.task_id = None
            return False

    # TODO: in cases where the task_id is updated to None, there should be some additional confirmation or step taken
    # TODO: in order to confirm the task is shut down and not lingering
    def status(self):
        """checks task status and returns info"""
        try:
            task = self.task_func.AsyncResult(self.task_id)
        # will result in ValueError is task_id is None
        except ValueError as e:
            return {'state': "NOT RUNNING"}

        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'successes': task.info.get('successes', 0),
            'failures': task.info.get('failures', 0),
            'sleeptime': task.info.get('sleeptime', 0),
            'current_url': task.info.get('current_url', ""),
            'next_url': task.info.get('next_url', ""),
            'status': task.info.get('status', '')
        }

        if task.state == 'PENDING':
            response['status'] = 'Pending...'
        elif task.state == 'PROGRESS':
            pass
        elif task.state == 'SUCCESS':
            self.task_id = None
            response['current'] = 1
            response['total'] = 1
        elif task.state == 'FAILURE':
            self.task_id = None
            if 'result' in task.info:
                response['result'] = task.info['result']
        else:
            self.task_id = None
            # something went wrong in the background job
            response['status'] = str(task.info)  # this is the exception raised

        return response

    def kill_task(self):
        try:
            task = self.task_func.AsyncResult(self.task_id)
        except ValueError:
            return None
        task.revoke(terminate=True)
        self.task_id = None