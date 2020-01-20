import os
import logging
import threading
import signal

class CleanupException(Exception):
    pass
class Cleanup:
    def __init__(self, challenges, interval=30):
        self.running = False
        self.exit = threading.Event()

        self.logger = logging.getLogger('cleanup')
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[{asctime}] [{module}] {levelname}: {message}', style='{'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG if os.getenv('DEBUG') else logging.INFO)

        self.challenges = challenges
        self.interval = interval

    def run(self):
        if self.running:
            raise CleanupException('Already running')

        self.running = True
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        self.logger.info('starting up')
        while not self.exit.is_set():
            self.logger.debug('running cleanup...')
            self.challenges.cleanup(self.logger)
            self.exit.wait(self.interval)

        self.logger.info('shutting down')
    def stop(self, _signum, _frame):
        self.exit.set()
