'''
Redis Publish Module
File added by Shubhadeep on 27-08-2020
'''
import json
import redis

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB_INDEX = 1
REDIS_AUTH = False
REDIS_PASSWORD = ''

if REDIS_AUTH:
    redis_server = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_INDEX)
else:
    redis_server = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_INDEX, 
        password=REDIS_PASSWORD)

def publish(channel_name, json_data):
    """Publish a json data to a redis channel
    Args:
        channel_name: name of the redis pubsub channel,
        json_data: data to publish (dict/string/int/float/list)
    Returns:
        tuple (success, message)
    """
    try:
        data_str = json.dumps(json_data)
        redis_server.publish(channel_name, data_str)
        # we will also queue the data in an array so that the data does not get lost
        redis_key = '{0}_saved'.format(channel_name)
        redis_server.sadd(redis_key, data_str)
        print ('Published on redis channel <{0}>, data <{1}>, redis key <{2}>'.format(channel_name, data_str, redis_key))
        return (True, 'Ok')
    except Exception as ex:
        print ('Redis error: {0}'.format(ex))
        return (False, 'Redis Publish Error: {0}'.format(ex))

    