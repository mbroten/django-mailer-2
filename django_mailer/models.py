from django.db import models
from django_mailer import constants, managers

from django import VERSION
if (VERSION[0] >= 1 and VERSION[1] >= 4):
    from django.utils.timezone import now
else:
    from datetime import datetime
    now = datetime.now

PRIORITIES = (
    (constants.PRIORITY_HIGH, 'high'),
    (constants.PRIORITY_NORMAL, 'normal'),
    (constants.PRIORITY_LOW, 'low'),
)

RESULT_CODES = (
    (constants.RESULT_SENT, 'success'),
    (constants.RESULT_SKIPPED, 'not sent (blacklisted)'),
    (constants.RESULT_FAILED, 'failure'),
)

class EmailMessageWrapper(object):
    """
    Mock functionality in django/core/mail/message.py for testing
    using file-based or other django MAIL_BACKENDs that expect
    message().as_string().
    """
    def __init__(self, encoded_message=''):
        self.encoded_message = encoded_message
    
    def as_string(self, unixfrom=False):
        return self.encoded_message
    
class Message(models.Model):
    """
    An email message.
    
    The ``to_address``, ``from_address`` and ``subject`` fields are merely for
    easy of access for these common values. The ``encoded_message`` field
    contains the entire encoded email message ready to be sent to an SMTP
    connection.
    
    """
    to_address = models.CharField(max_length=200)
    from_address = models.CharField(max_length=200)
    subject = models.CharField(max_length=255)

    encoded_message = models.TextField()
    date_created = models.DateTimeField(default=now)

    class Meta:
        ordering = ('date_created',)

    @property
    def encoded_from_address(self):
        return self.from_address.encode('utf-8')

    @property
    def encoded_to_address(self):
        return self.to_address.encode('utf-8')

    def message(self):
        return EmailMessageWrapper(self.encoded_message)
        
    def __unicode__(self):
        return '%s: %s' % (self.to_address, self.subject)


class QueuedMessage(models.Model):
    """
    A queued message.
    
    Messages in the queue can be prioritised so that the higher priority
    messages are sent first (secondarily sorted by the oldest message).
    
    """
    message = models.OneToOneField(Message, editable=False)
    priority = models.PositiveSmallIntegerField(choices=PRIORITIES,
                                            default=constants.PRIORITY_NORMAL)
    deferred = models.DateTimeField(null=True, blank=True)
    retries = models.PositiveIntegerField(default=0)
    date_queued = models.DateTimeField(default=now)

    objects = managers.QueueManager()

    class Meta:
        ordering = ('priority', 'date_queued')

    def defer(self):
        self.deferred = now()
        self.save()


class Blacklist(models.Model):
    """
    A blacklisted email address.
    
    Messages attempted to be sent to e-mail addresses which appear on this
    blacklist will be skipped entirely.
    
    """
    email = models.EmailField(max_length=200)
    date_added = models.DateTimeField(default=now)

    class Meta:
        ordering = ('-date_added',)
        verbose_name = 'blacklisted e-mail address'
        verbose_name_plural = 'blacklisted e-mail addresses'


class Log(models.Model):
    """
    A log used to record the activity of a queued message.
    
    """
    message = models.ForeignKey(Message, editable=False)
    result = models.PositiveSmallIntegerField(choices=RESULT_CODES)
    date = models.DateTimeField(default=now)
    log_message = models.TextField()

    class Meta:
        ordering = ('-date',)
