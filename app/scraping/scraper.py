from flask import current_app, url_for, jsonify

class Scraper:
    def __init__(self, name, task_func):
        self.name = name
        self.task_id = None
        self.task_func = task_func

    def start_task(self):
        """starts the task and returns basic info"""
        if self.task_id:
            if self.status()['state'] != "PENDING":
                self.task_id = None
        if self.task_id == None:
            task = self.task_func.apply_async()
            self.task_id = task.id
        return jsonify({}), 202, {'Location': url_for('scraping.check_status', scraper_name=self.name)}

    def is_running(self):
        # a harder check on whether or not this is running
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
        except ValueError:
            return {'state': "NOT RUNNING"}

        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'current': 0,
                'successes': 0,
                'failures': 0,
                'total': 1,
                'sleeptime': 0,
                'status': 'Pending...'
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'successes': task.info.get('successes', 0),
                'failures': task.info.get('failures', 0),
                'sleeptime': task.info.get('sleeptime', 0),
                'status': task.info.get('status', '')
            }
        elif task.state == 'SUCCESS':
            self.task_id = None
            response = {
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'successes': task.info.get('successes', 0),
                'failures': task.info.get('failures', 0),
                'sleeptime': task.info.get('sleeptime', 0),
                'status': task.info.get('status', '')
            }
        elif task.state == 'FAILURE':
            self.task_id = None
            response = {
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'successes': task.info.get('successes', 0),
                'failures': task.info.get('failures', 0),
                'sleeptime': task.info.get('sleeptime', 0),
                'status': task.info.get('status', '')
            }
            if 'result' in task.info:
                response['result'] = task.info['result']
        else:
            self.task_id = None
            # something went wrong in the background job
            response = {
                'state': task.state,
                'current': 1,
                'successes': 0,
                'failures': 0,
                'total': 1,
                'sleeptime': 0,
                'status': str(task.info),  # this is the exception raised
            }
        return response

    def kill_task(self):
        try:
            task = self.task_func.AsyncResult(self.task_id)
        except ValueError:
            return None
        task.revoke(terminate=True)