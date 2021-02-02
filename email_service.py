"""
A parallel multiprocessing queue using Redis
Developer - Shubhadeep
"""
from logging.handlers import RotatingFileHandler
import logging as email_logging
import json
import redis
import time
import _thread
import multiprocessing
import queue
import random
import pymysql
import datetime
import smtplib
import ssl
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.conf import settings

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SSIL_SSO_MS.settings')

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB_INDEX = 1
REDIS_AUTH = False
REDIS_PASSWORD = ''
REDIS_CHANNEL = 'email'
REDIS_KEY = '{0}_saved'.format(REDIS_CHANNEL)
MAX_PROCESS = 3

DB_SETTINGS = settings.DATABASES['default']
MYSQL_HOST = 'localhost'
MYSQL_PORT = int(DB_SETTINGS['PORT'])
MYSQL_USER = DB_SETTINGS['USER']
MYSQL_PASSWORD = DB_SETTINGS['PASSWORD']
MYSQL_DB = DB_SETTINGS['NAME']

MAIL_CONFIGURATION = {
    'default': {
        'EMAIL_FROM': settings.EMAIL_FROM,
        'EMAIL_HOST': settings.EMAIL_HOST,
        'EMAIL_PORT': settings.EMAIL_PORT,
        'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
        'EMAIL_HOST_PASSWORD': settings.EMAIL_HOST_PASSWORD,
    },
    'hr': {
        'EMAIL_FROM': settings.HR_EMAIL_FROM,
        'EMAIL_HOST': settings.HR_EMAIL_HOST,
        'EMAIL_PORT': settings.HR_EMAIL_PORT,
        'EMAIL_HOST_USER': settings.HR_EMAIL_HOST_USER,
        'EMAIL_HOST_PASSWORD': settings.HR_EMAIL_HOST_PASSWORD,
    }
}
# HR_EMAIL_CODES = ['TEST001']
HR_EMAIL_CODES = ['HRMS-5P-R', 'HRMS-5p-C', 'HRMS-5P-RH-1R',  'HRMS-5P-1R',
                  'HRMS-5P-RR-RH', 'HRMS-5P-R-RH',  'HRMS-3P-RR-RH', 'HRMS-3P-R-RH',
                  'HRMS-3P-RH-1R', 'HRMS-3P-RH-R', 'HRMS-3P-R',  'HRMS-3P-1R', 'ATP-PM-EW',
                  'AT-URAFE', 'AT-PRAAFRH']

formatter = email_logging.Formatter('%(asctime)s %(levelname)s %(message)s')


def setup_logger():
    handler = RotatingFileHandler('email_service.log', maxBytes=20000, backupCount=3)
    handler.setFormatter(formatter)
    logger = email_logging.getLogger('email_service')
    logger.setLevel(email_logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(email_logging.StreamHandler())
    return logger


email_logger = setup_logger()


class Worker(multiprocessing.Process):
    """
    Developer - Shubhadeep
    Demo Worker Class
    """

    def __init__(self, str_data, index):
        """
        Constructor
        """
        self.str_data = str_data
        self.index = index
        self.redis_server = None
        multiprocessing.Process.__init__(self)
        # add any custom initialize functions below

    def connect_redis(self):
        if REDIS_AUTH:
            self.redis_server = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_INDEX)
        else:
            self.redis_server = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_INDEX,
                                                  password=REDIS_PASSWORD)

    def run(self):
        entry_id, con = None, None
        try:
            redis_data = json.loads(self.str_data)
            entry_id = int(redis_data[0])
        except:
            email_logger.info('Could not read entry id from {0}'.format(self.str_data))
        self.connect_redis()
        if entry_id:
            email_logger.info('Processing Email - entry id {0}'.format(entry_id))
            con = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                                  password=MYSQL_PASSWORD, database=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)
            with con.cursor() as cur:
                update_stmt = ''
                try:
                    cur.execute('SELECT * FROM mail_history where id={0}'.format(entry_id))
                    entry = cur.fetchone()
                    code, recipient_list, cc, bcc, subject, body, attachment = entry['code'], json.loads(entry['recipient_list']),\
                                                                               json.loads(entry['cc']),json.loads(entry['bcc']),\
                                                                               entry['subject'],  entry['body'],  entry['attachment']
                    send_email(code, subject, body, cc, bcc, recipient_list, attachment=attachment)
                    update_stmt = """update mail_history set status = 'sent' where id = {0}""".format(entry_id)
                except Exception as ex:
                    msg = str(ex).replace("'", "")
                    email_logger.info('Exception in entry id {0} : {1}'.format(entry_id, msg))
                    update_stmt = """update mail_history set status = 'error', error_msg = '{0}' where id = {1}""".format(msg, entry_id)
                cur.execute(update_stmt)
                con.commit()
        self.redis_server.srem(REDIS_KEY, self.str_data)
        if con:
            con.close()


def send_email(code: str, subject: str, body: str, cc: list, bcc: list, recipient_list: list, attachment: str = None):
    config_code = 'default'
    if code in HR_EMAIL_CODES:
        config_code = 'hr'

    mail_config = MAIL_CONFIGURATION[config_code]

    email_logger.info('Sending email : code {0}, config code {1}, subject {2}'.format(code, config_code, subject))

    sender_email = mail_config['EMAIL_FROM']
    receiver_email = ", ".join(recipient_list)
    cc = ", ".join(cc)
    bcc = ", ".join(bcc)
    password = mail_config['EMAIL_HOST_PASSWORD']

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    message["Cc"] = cc
    message["Bcc"] = bcc

    part1 = MIMEText(body, "html")
    message.attach(part1)

    with smtplib.SMTP(mail_config['EMAIL_HOST'], mail_config['EMAIL_PORT']) as server:
        server.starttls()
        server.login(sender_email, password)
        if attachment:
            if code == "PMS-ST-A":
                attachment = '.' + attachment
                fp = open(attachment, 'rb')
                mime_image = MIMEImage(fp.read())
                fp.close()
                mime_image.add_header('Content-ID', '<image>')
                message.attach(mime_image)
            if code in ["ETAP", "ETRDC", 'ET-EUR', 'ETAP-SU', 'DRDC', 'TEST001']:
                part = MIMEText(attachment, 'calendar')
                part.add_header('Filename', 'calendar.ics')
                part.add_header('Content-Disposition', 'attachment; filename=calendar.ics')
                message.attach(part)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )

    email_logger.info('Email sent to {0}, Email Code {1}, attachment size {2}'.format(recipient_list,
                                                                                      code, len(attachment)))


class RedisSubscriber:
    """
    Developer - Shubhadeep
    DO NOT UPDATE THIS CLASS, FOR ANY iSSUES PLEASE CONTACT
    """
    redis_server = None
    running = True
    index = 0
    workers = {}
    handler_thread = None
    message_queue = queue.Queue()

    def __init__(self):
        pass

    def connect(self):
        if REDIS_AUTH:
            self.redis_server = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_INDEX)
        else:
            self.redis_server = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_INDEX,
                                                  password=REDIS_PASSWORD)

    def run_subscriber(self):
        _thread.start_new_thread(self.queue_handler, ())
        while self.running:
            try:
                email_logger.info('Connecting to Redis Server on {0}:{1}, db index {2}'.format(REDIS_HOST, REDIS_PORT, REDIS_DB_INDEX))
                self.connect()
                existing_queue = self.redis_server.smembers(REDIS_KEY)
                for msg in existing_queue:
                    self.message_queue.put((msg.decode("utf-8"), self.index))
                    self.index += 1
                email_logger.info('Unprocessed data count - {0}'.format(self.message_queue.qsize()))
                pubsub = self.redis_server.pubsub()
                pubsub.subscribe(REDIS_CHANNEL)
                while self.running:
                    msg = pubsub.get_message()
                    if msg:
                        if msg['type'] == 'message':
                            self.event_handler(msg['channel'].decode("utf-8"),
                                               msg['data'].decode("utf-8"))
                        elif msg['type'] == 'subscribe':
                            email_logger.info('Subscribed to channel: {0}'.format(REDIS_CHANNEL))
                    time.sleep(0.1)
            except Exception as ex:
                email_logger.error('Redis Subscription error: {0}'.format(ex))
                time.sleep(5)
            except:
                self.running = False
        email_logger.info('Stopped!')

    def event_handler(self, channel, str_data):
        email_logger.info('Redis message on channel: {0}, index: {2}, data string: {1}'.format(channel, str_data, self.index))
        self.message_queue.put((str_data, self.index))
        self.index += 1

    def queue_handler(self):
        while self.running:
            try:
                keys = self.workers.keys()
                for idx in keys:
                    if not self.workers[idx].is_alive():
                        del self.workers[idx]
                running = len(self.workers.keys())
                if running < MAX_PROCESS:
                    qsize = self.message_queue.qsize()
                    new = MAX_PROCESS - running
                    new = new if qsize > new else qsize
                    if new:
                        email_logger.info('Running {0} of {1} parallel tasks, {2} items in queue, starting {3} new tasks..'.format(
                            running, MAX_PROCESS, qsize, new))
                        for i in range(new):
                            message, index = self.message_queue.get()
                            p = Worker(message, index)
                            self.workers[index] = p
                            p.start()
                time.sleep(5)
            except:
                pass


if __name__ == '__main__':
    sub = RedisSubscriber()
    sub.run_subscriber()
