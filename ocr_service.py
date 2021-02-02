"""
A parallel multiprocessing queue using Redis
Developer - Shubhadeep
"""
import json
import redis
import time
import _thread
import multiprocessing
import queue
import random
import pymysql
import datetime

from pdf2image import convert_from_path
import os
import tempfile
from PIL import Image
import pytesseract
import cv2
import datetime
import camelot

import SSIL_SSO_MS.settings as settings

import logging as ocr_logging
from logging.handlers import RotatingFileHandler
formatter = ocr_logging.Formatter('%(asctime)s %(levelname)s %(message)s')


def setup_logger():
    handler = RotatingFileHandler('ocr_service.log', maxBytes=20000, backupCount=5)
    handler.setFormatter(formatter)
    logger = ocr_logging.getLogger('ocr_service')
    logger.setLevel(ocr_logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(ocr_logging.StreamHandler())
    return logger


logger = setup_logger()

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB_INDEX = 1
REDIS_AUTH = False
REDIS_PASSWORD = ''
REDIS_CHANNEL = 'ocr'
REDIS_KEY = '{0}_saved'.format(REDIS_CHANNEL)
MAX_PROCESS = 3

DB_SETTINGS = settings.DATABASES['default']
MYSQL_HOST = 'localhost'
MYSQL_PORT = int(DB_SETTINGS['PORT'])
MYSQL_USER = DB_SETTINGS['USER']
MYSQL_PASSWORD = DB_SETTINGS['PASSWORD']
MYSQL_DB = DB_SETTINGS['NAME']


temp_dir = 'ocr_temp'
data_list_fields = ['bat_no', 'cement', 'fly_ash', 'sand', 'agg_20mm',
                    'agg_10mm', 'water', 'admixture']

# Rj : {0: 'Bat.No', 1: 'Time', 2: '', 3: 'Cycle\ntime', 4: 'SAND', 5: 'SAND', 6: '10 MM', 7: '20 MM', 8: '0', 9: 'CEMENT', 10: '0', 11: '0', 12: 'FLY \nASH', 13: 'water\nWATER\ncorr', 14: 'ADDITIVE', 15: '0', 16: 'TOTAL'}
data_list_field_map = {
    # 'KD': ['{0}', '{5}', '{6}', '{2}', '{3}', '{4}', '{7}', '{8}'],
    # 'RJ': ['{0}', '{5}', '{6}', '{1}', '{4}', '{3}', '{7}', '{8}'],
    'KD': ['{0}', '{9}', '{12}', '{4} + {5}', '{6}', '{7}', '{13}', '{14}'],
    'RJ': ['{0}', '{9}', '{12}', '{4}', '{7}', '{6}', '{13}', '{14}'],
    'MT': ['{incr}', '{4}', '{5}', '({1} + {3})', '{0}', '{2}', '{6}', '({9} / 1000)']
}
allowed_special, allowed_special_txt = ['.'], [':',',','/','.']
replaces, replaces_txt = [('@', '0'),('\n', ' '),('(',''),(')','')], [('\n',','),(':,',':')]

process_thresh = False
pid = os.getpid()

if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

def clean_pdf_text(type_code, txt, data_type='number'):
    formatted_line = []
    spcl, rplcs = allowed_special, replaces
    if data_type=="txt":
        spcl = allowed_special_txt
        rplcs = replaces_txt
    for r in rplcs:
        txt = txt.replace(r[0], r[1])
    if data_type == 'number':
        return txt.strip()
    else:
        for i, char in enumerate(list(txt)):
            if (char.isalpha() or char.isdigit()
                    or char in spcl):
                formatted_line += char
        return strip("".join(formatted_line))

def clean_up(type_code, txt):
    formatted_lines, all_lines = [], txt.split('\n')
    space_count = 0
    for line in all_lines:
        line = str(line).upper()
        for r in replaces:
            line = line.replace(r[0], r[1])
        formatted_line = []
        for i, char in enumerate(list(line)):
            if (char.isalpha() or char.isdigit()
                    or char in allowed_special):
                if space_count and char in allowed_special:
                    pass
                else:
                    formatted_line += char
                    space_count = 0
            elif char == ' ':
                space_count += 1
                if space_count == 1:
                    formatted_line += ' '
        formatted_line = strip("".join(formatted_line))
        if len(formatted_line) > 0:
            formatted_lines.append(formatted_line)
    return formatted_lines


def strip(val, num=False):
    val = val.strip()
    for char in allowed_special:
        val = val.strip(char)
    if num:
        new_val = ''
        for c in val:
            if c.isdigit() or c == '.':
                new_val += c
            new_val = new_val.lstrip('0')
        val = new_val if len(new_val) > 0 else '0'
    return val.strip()


def get_value_from_key(type_code, line, keys):
    line = ' ' + line
    values = []
    for key in keys:
        splitted = line.split(key)
        line = splitted[1]
        value = strip(splitted[0])
        if len(value) > 0:
            values.append(value)
    value = strip(line)
    if len(value) > 0:
        values.append(value)
    return values


def parse(type_code, lines):
    concrete = ''
    date = datetime.datetime.now()
    qty = 0.0
    list_data = []
    if type_code == 'KD' or type_code == 'RJ':
        list_start_index, list_end_index = None, None
        for index, line in enumerate(lines):
            if 'BATCH DATE' in str(line):
                try:
                    str_array = get_value_from_key(type_code, line, ['BATCH DATE', 'BATCH START TIME'])
                    date = datetime.datetime.strptime(' '.join(str_array), '%d%m%Y %H%M%S')
                    if abs(date.year - datetime.datetime.now().year > 1):
                        date = date.replace(year=datetime.datetime.now().year)
                except Exception as ex:
                    logger.info('Exception in Date : {0}'.format(ex))
            if 'RECIPE NUMBER' in str(line):
                try:
                    str_array = get_value_from_key(type_code, line, ['RECIPE NUMBER', 'RECIPE NAME'])
                    concrete = strip(str_array[1])
                except Exception as ex:
                    logger.info('Exception in Recipe : {0}'.format(ex))
            if 'BATCH SIZE' in str(line):
                try:
                    str_array = get_value_from_key(type_code, line, ['BATCH SIZE'])
                    qty = float(strip(' '.join(str_array)))
                except Exception as ex:
                    logger.info('Exception in Batch Size : {0}'.format(ex))

            if line.startswith('BAT '):
                list_start_index = index + 2
            if list_start_index is not None and list_end_index is None and list_start_index <= index:
                data_parts_str = line.split(' ')
                if len(data_parts_str) >= 11 and not 'SAND' in line:
                    data_parts_dict = {v: strip(k, num=True) for v, k in enumerate(data_parts_str)}
                    data_list_item = {}
                    for field_idx, field_name in enumerate(data_list_fields):
                        formula = data_list_field_map[type_code][field_idx]
                        for key in data_parts_dict:
                            formula = formula.replace('{' + str(key) + '}', data_parts_dict[key])
                        try:
                            if field_name == 'bat_no':
                                data_list_item[field_name] = int(formula)
                            else:
                                data_list_item[field_name] = float(formula)
                        except Exception as ex:
                            logger.info('Exception in Data item {2} : {1}, formula : {0}'.format(formula, ex, field_name))
                            data_list_item[field_name] = 0
                    list_data.append(data_list_item)
                else:
                    list_end_index = index

        qty = qty * len(list_data)

    elif type_code == 'MT':
        list_start_index, list_end_index, found_entry = None, None, False
        for index, line in enumerate(lines):
            print(index, line)
            if line.startswith('REC'):
                continue
            if not found_entry:
                print('started reading', index)
                found_entry = True
                parts = line.split(' ')
                try:
                    concrete = strip(parts[0])
                except Exception as ex:
                    logger.info('Exception in Recipe : {0}'.format(ex))
                try:
                    qty = float(strip(parts[1]))
                except Exception as ex:
                    logger.info('Exception in Batch Size : {0}'.format(ex))
                try:
                    date = datetime.datetime.strptime('{0} {1}'.format(strip(parts[2]), strip(parts[3])), '%d%m%Y %H%M%S')
                    if abs(date.year - datetime.datetime.now().year > 1):
                        date = date.replace(year=datetime.datetime.now().year)
                except Exception as ex:
                    logger.info('Exception in Date : {0}'.format(ex))
            else:
                data_parts_str = line.split(' ')
                if data_parts_str[0].isnumeric():
                    list_start_index = index
                    print('list_start_index', list_start_index)
                if list_start_index is not None and list_end_index is None and list_start_index <= index:
                    print('data_parts_str', data_parts_str)
                    if len(data_parts_str) >= 11 and not 'A' in line:
                        data_parts_dict = {v: strip(k, num=True) for v, k in enumerate(data_parts_str)}
                        data_parts_dict['incr'] = str(len(list_data) + 1)
                        data_list_item = {}
                        for field_idx, field_name in enumerate(data_list_fields):
                            formula = data_list_field_map[type_code][field_idx]
                            for key in data_parts_dict:
                                formula = formula.replace('{' + str(key) + '}', clean_up(data_parts_dict[key]))
                            try:
                                data_list_item[field_name] = eval(formula)
                            except Exception as ex:
                                logger.info('Exception in Data item {2} : {1}, formula : {0}'.format(formula, ex, field_name))
                                data_list_item[field_name] = 0
                        list_data.append(data_list_item)
                    else:
                        list_end_index = index
    return (concrete, date, qty, list_data)


def match_grade_name(grade_txt, grade_names):
    print (grade_names)
    grade_txt = strip(grade_txt).lower().replace(' ', '')
    max, index = 0, -1
    for i, name in enumerate(grade_names):
        name = strip(name).lower()
        index_score = 0
        c_idx_last = -1
        for c in grade_txt:
            try:
                c_idx = name.index(c)
                if c_idx - c_idx_last == 1 or c_idx_last == -1:
                    index_score += 1
                c_idx_last = c_idx
            except:
                c_idx = None
        current = index_score
        if current > max:
            max = current
            index = i
    return grade_names[index] if index > -1 else ''


def ocr(type_code, jpeg_path, png_path, grade_names, txt_path=None):
    image = cv2.imread(jpeg_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if process_thresh:
        gray = cv2.threshold(gray, 0, 255,
                             cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    cv2.imwrite(png_path, gray)
    text = pytesseract.image_to_string(Image.open(png_path), lang='eng', config='--psm 6 --oem 3')

    lines = clean_up(type_code, text)
    if txt_path:
        with open(txt_path, "w") as f:
            for l in lines:
                f.write(l + '\n')

    concrete, dt, qty, list_data = parse(type_code, lines)
    logger.info('**** OCR Results ****')
    logger.info('-----------------------')
    logger.info('concrete grade : {0}'.format(concrete))
    logger.info('date : {0}'.format(dt))
    logger.info('quantity : {0}'.format(qty))
    logger.info('batch data:')
    for data_list_item in list_data:
        logger.info('\t' + str(data_list_item))
    if len(list_data) == 0:
        logger.info('\t <No list data>')
    logger.info('-----------------------')
    logger.info('Available Grades {0}'.format(grade_names))
    concrete = match_grade_name(concrete, grade_names)
    logger.info('Matched Grade {0}'.format(concrete))
    os.remove(jpeg_path)
    os.remove(png_path)
    cv2.waitKey(0)
    return (concrete, dt, qty, list_data)

def text_parse(type_code, txt_path, grade_names):
    with open(txt_path, 'r') as f:
        text = f.read()
        lines = clean_up(type_code, text)
        concrete, dt, qty, list_data = parse(type_code, lines)
        logger.info('**** TXT Parse Results ****')
        logger.info('-----------------------')
        logger.info('concrete grade : {0}'.format(concrete))
        logger.info('date : {0}'.format(dt))
        logger.info('quantity : {0}'.format(qty))
        logger.info('batch data:')
        for data_list_item in list_data:
            logger.info('\t' + str(data_list_item))
        if len(list_data) == 0:
            logger.info('\t <No list data>')
        logger.info('-----------------------')
        logger.info('Available Grades {0}'.format(grade_names))
        concrete = match_grade_name(concrete, grade_names)
        logger.info('Matched Grade {0}'.format(concrete))
        return (concrete, dt, qty, list_data)

def pdf_parse(type_code, pdf_path, grade_names):
    tables = camelot.read_pdf(pdf_path)
    concrete, dt, qty, list_data = None, None, None, []
    data_started, pdf_type = False, 1
    for i, row in tables[0].df.iterrows():
        values = list(row.values)
        # print (values)
        if len(values):
            if data_started:
                if values[0] == '':
                    break
                if pdf_type == 2:
                    values0_parts = values[0].split('\n')
                    values[0] = values0_parts[1]
                    values.insert(1, values0_parts[0])
                    values.insert(2, '')
                    values.insert(3, values0_parts[2])
                    values[4] = values[5]
                    del values[5]
                    print (data_parts_dict)
                data_parts_dict = {v: strip(k) for v, k in enumerate(values)}
                data_list_item = {}
                for field_idx, field_name in enumerate(data_list_fields):
                    formula = data_list_field_map[type_code][field_idx]
                    for key in data_parts_dict:
                        formula = formula.replace('{' + str(key) + '}', clean_pdf_text(type_code, data_parts_dict[key]))
                        # if field_name == 'water':
                        #     print (data_parts_dict[key], formula)
                    try:
                        if field_name == 'bat_no':
                            data_list_item[field_name] = int(formula)
                        elif field_name == 'water':
                            parts = str(formula).split(' ')
                            data_list_item[field_name] = float(parts[0]) + float(parts[2])
                        else:
                            data_list_item[field_name] = eval(formula)
                    except Exception as ex:
                        logger.info('Exception in Data item {2} : {1}, formula : {0}'.format(formula, ex, field_name))
                        data_list_item[field_name] = 0
                # print ('----------------------------------')
                # print (data_list_item)
                list_data.append(data_list_item)
            elif values[0].startswith('Bat.No'):
                data_parts_dict = {v: strip(k) for v, k in enumerate(values)}
                data_started = True
            elif 'Bat.No' in values[0]:
                data_parts_dict = {v: strip(k) for v, k in enumerate(values)}
                data_started = True
                pdf_type = 2
            else:
                if data_started:
                    break
                header = clean_pdf_text(type_code, values[0], data_type='txt')
                # print ('header data', header)
                if 'CustomerName:BatchDate:SetBatches:' in header:
                    # print (header)
                    qty = header.split('BatchSize:')[1].split(',')[0]
                    order_name = header.split('RecipeName:')[1].split(',')[0]
                    concrete = match_grade_name(order_name, grade_names)
                    _date = header.split(',')[2]
                    _time = header.split(',')[4]
                    # 15/12/2020 7:17:04pm
                    dt = datetime.datetime.strptime('{0} {1}'.format(_date, _time.upper()), '%d/%m/%Y %I:%M:%S%p')
        else:
            print ('EMPTY ARRAY!')
            break
    print ('END, Data Count', len(list_data))
    # fd = open(pdf_path, "rb")
    # viewer = SimplePDFViewer(fd)
    # txt = ''
    # for canvas in viewer:
    #     txt = canvas.strings
    # print (txt)

    return (concrete, dt, qty, list_data)
    
    # with open(txt_path, 'r') as f:
    #     text = f.read()
    #     lines = clean_up(type_code, text)
    #     concrete, dt, qty, list_data = parse(type_code, lines)
    #     logger.info('**** TXT Parse Results ****')
    #     logger.info('-----------------------')
    #     logger.info('concrete grade : {0}'.format(concrete))
    #     logger.info('date : {0}'.format(dt))
    #     logger.info('quantity : {0}'.format(qty))
    #     logger.info('batch data:')
    #     for data_list_item in list_data:
    #         logger.info('\t' + str(data_list_item))
    #     if len(list_data) == 0:
    #         logger.info('\t <No list data>')
    #     logger.info('-----------------------')
    #     logger.info('Available Grades {0}'.format(grade_names))
    #     concrete = match_grade_name(concrete, grade_names)
    #     logger.info('Matched Grade {0}'.format(concrete))
    #     return (concrete, dt, qty, list_data)

def convert_pdf(file_path, output_path):
    # save temp image files in temp dir, delete them after we are finished
    with tempfile.TemporaryDirectory() as temp_dir:
        # convert pdf to multiple image
        images = convert_from_path(file_path, output_folder=temp_dir)
        # save images to temporary directory
        temp_images = []
        for i in range(len(images)):
            image_path = f'{temp_dir}/{i}.jpg'
            images[i].save(image_path, 'JPEG')
            temp_images.append(image_path)
        # read images into pillow.Image
        imgs = list(map(Image.open, temp_images))
    # find minimum width of images
    min_img_width = min(i.width for i in imgs)
    # find total height of all images
    total_height = 0
    for i, img in enumerate(imgs):
        total_height += imgs[i].height
    # create new image object with width and total height
    merged_image = Image.new(imgs[0].mode, (min_img_width, total_height))
    # paste images together one by one
    y = 0
    for img in imgs:
        merged_image.paste(img, (0, y))
        y += img.height
    # save merged image
    merged_image.save(output_path)
    return output_path


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

    def get_entry_data(self, redis_data):
        try:
            return (int(redis_data[0]), redis_data[1], redis_data[2])
        except:
            return (None, None, None)

    def run(self):
        try:
            redis_data = json.loads(self.str_data)
        except Exception as e:
            logger.info('Unable to read json data {0}'.format(self.str_data))
            redis_data = None
        entry_id, type_code, file_path = self.get_entry_data(redis_data)
        self.connect_redis()
        if entry_id:
            logger.info('Processing OCR - entry id {0}, project code {1}, file {2}'.format(entry_id, type_code, file_path))

            # for dev only
            # if type_code == 'RJ':
            #     type_code = 'KD'
            #     file_path = '/home/shubhadeep/Downloads/KD/KD12.pdf'
                # file_path = '/home/shubhadeep/Downloads/RJ/RJ1.pdf'
            # ---

            con = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                                  password=MYSQL_PASSWORD, database=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor)
            with con.cursor() as cur:
                try:
                    cur.execute('SELECT * FROM pms_batching_plant_batching_entry where id={0}'.format(entry_id))
                    entry = cur.fetchone()
                    logger.info('Deleting previous entry details of id {0}..'.format(entry_id))
                    delete_stmt = "delete from pms_batching_plant_batching_entry_details where batching_entry_id={0}".format(entry_id)
                    cur.execute(delete_stmt)
                    cur.execute('SELECT * FROM pms_batching_plant_concrete_master')
                    concretes = cur.fetchall()
                    grade_names = [c['concrete_name'] for c in concretes]
                    if str(file_path).lower().endswith('.pdf'):
                        if type_code in ['KD', 'RJ']:
                            concrete, dt, qty, list_data = pdf_parse(type_code, file_path, grade_names)    
                            # print (concrete, dt, qty, list_data)
                            # return
                        else:
                            jpeg_path = os.path.join(temp_dir, '{0}.jpg'.format(entry_id))
                            png_path = os.path.join(temp_dir, '{0}.png'.format(entry_id))
                            convert_pdf(file_path, jpeg_path)
                            concrete, dt, qty, list_data = ocr(type_code, jpeg_path, png_path, grade_names)
                    elif str(file_path).lower().endswith('.txt') or str(file_path).lower().endswith('.text'):
                        concrete, dt, qty, list_data = text_parse(type_code, file_path, grade_names)
                    if concrete != '':
                        grade_id = [c['id'] for c in concretes if c['concrete_name'] == concrete][0]
                        date = dt.strftime('%Y-%m-%d %H:%M:%S')
                        update_stmt = """update pms_batching_plant_batching_entry
                            set concrete_master_id = {0}, concrete_quantity = {1}, document_status = 3,
                            document_processed_at = '{2}', batch_processed_at = '{2}'
                            where id = {3}""".format(grade_id, qty, date, entry_id)
                        cur.execute(update_stmt)
                        for data in list_data:
                            bat_no = data['bat_no']
                            cement = data['cement']
                            fly_ash = data['fly_ash']
                            sand = data['sand']
                            agg_20mm = data['agg_20mm']
                            agg_10mm = data['agg_10mm']
                            water = data['water']
                            admixture = data['admixture']
                            insert_stmt = f"""INSERT INTO `pms_batching_plant_batching_entry_details`
                                        (`bat_no`,
                                        `cement`,
                                        `fly_ash`,
                                        `sand`,
                                        `agg_20mm`,
                                        `agg_10mm`,
                                        `water`,
                                        `admixture`,
                                        `batching_entry_id`,
                                        `is_deleted`)
                                        VALUES
                                        ({bat_no},
                                        {cement},
                                        {fly_ash},
                                        {sand},
                                        {agg_20mm},
                                        {agg_10mm},
                                        {water},
                                        {admixture},
                                        {entry_id}, 
                                        {'0'});"""
                            cur.execute(insert_stmt)
                        con.commit()
                        logger.info('Successfully processed entry id {0}'.format(entry_id))
                    else:
                        raise Exception('Could not detect concrete grade!')
                except Exception as ex:
                    raise Exception(ex)
                    # msg = str(ex).replace("'", "")
                    # logger.info('Exception in entry id {0} : {1}'.format(entry_id, msg))
                    # update_stmt = """update pms_batching_plant_batching_entry set
                    #     document_status = 4, error_msg = '{0}'
                    #     where id = {1}""".format(msg, entry_id)
                    # cur.execute(update_stmt)
                    # con.commit()
            con.close()
        else:
            logger.info("Invalid entry id in redis data {0}".format(redis_data))

        self.redis_server.srem(REDIS_KEY, self.str_data)
        return


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
                logger.info('Connecting to Redis Server..')
                self.connect()
                existing_queue = self.redis_server.smembers(REDIS_KEY)
                for msg in existing_queue:
                    self.message_queue.put((msg.decode("utf-8"), self.index))
                    self.index += 1
                logger.info('Unprocessed data count - {0}'.format(self.message_queue.qsize()))
                pubsub = self.redis_server.pubsub()
                pubsub.subscribe(REDIS_CHANNEL)
                while self.running:
                    msg = pubsub.get_message()
                    if msg:
                        if msg['type'] == 'message':
                            self.event_handler(msg['channel'].decode("utf-8"),
                                               msg['data'].decode("utf-8"))
                        elif msg['type'] == 'subscribe':
                            logger.info('Subscribed to channel: {0}'.format(REDIS_CHANNEL))
                    time.sleep(0.1)
            except Exception as ex:
                logger.info('Redis Subscription error: {0}'.format(ex))
                time.sleep(5)
            except:
                self.running = False
        logger.info('Stopped!')

    def event_handler(self, channel, str_data):
        logger.info('Redis message on channel: {0}, index: {2}, data string: {1}'.format(channel, str_data, self.index))
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
                        logger.info('Running {0} of {1} parallel tasks, {2} items in queue, starting {3} new tasks..'.format(
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
