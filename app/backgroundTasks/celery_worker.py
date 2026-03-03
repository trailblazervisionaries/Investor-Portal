from app.backgroundTasks.MonitorAsync import celery_app

if __name__ == "__main__":

    celery_app.start(argv=['worker', '--loglevel=info', '--pool=threads', '--concurrency=4', '-n', 'ip_app@%h'])