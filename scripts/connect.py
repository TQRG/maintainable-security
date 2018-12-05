from utils import *
import redis

# connect to the database
def connect_to_db(cf_filename):
    try:
        redis_cf = load_cf_file(cf_filename)
        # redis connection
        r = redis.Redis(
            host=redis_cf['redis']['host'],
            port=redis_cf['redis']['port'],
            password=redis_cf['redis']['password'],
            charset='utf-8',
            decode_responses=True)
        print('Succesfully connected to the database!')
        return r
    except Exception as ex:
        print('Error:', ex)
        exit('Failed to connect, terminating.')