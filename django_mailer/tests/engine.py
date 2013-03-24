from django.test import TestCase
from django_mailer import engine
from zc.lockfile import LockFile
from StringIO import StringIO
import logging


class LockTest(TestCase):
    """
    Tests for Django Mailer trying to send mail when the lock is already in
    place.
    """

    def setUp(self):
        # Create somewhere to store the log debug output.
        self.output = StringIO()
        # Create a log handler which can capture the log debug output.
        self.handler = logging.StreamHandler(self.output)
        self.handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        self.handler.setFormatter(formatter)
        # Add the log handler.
        logger = logging.getLogger('django_mailer')
        logger.addHandler(self.handler)

        # Use a test lock-file name in case something goes wrong, then emulate
        # that the lock file has already been acquired by another process.
        self.original_lock_path = engine.LOCK_PATH
        engine.LOCK_PATH += '.mailer-test'
        self.lock = LockFile(engine.LOCK_PATH)

    def tearDown(self):
        # Remove the log handler.
        logger = logging.getLogger('django_mailer')
        logger.removeHandler(self.handler)

        # Revert the lock file unique name
        engine.LOCK_PATH = self.original_lock_path
        self.lock.close()

    def test_locked(self):
        # Acquire the lock so that send_all will fail.
        engine.send_all()
        self.output.seek(0)
        self.assertEqual(self.output.readlines()[-1].strip(),
                         'Lock already in place. Exiting.')
