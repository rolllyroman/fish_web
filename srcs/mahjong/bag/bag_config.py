import redis
import pymysql

bag_redis = redis.Redis(host='127.0.0.1',password="168joyvick",db="2")
#bag_redis = redis.Redis(host='120.79.135.194',password="168joyvick",db="2")
game_redis = redis.Redis(host='127.0.0.1',password="168joyvick",db="1")


class Mysql_instance(object):
    def __init__(self,host="127.0.0.1",port=3306,user="root",passwd="168mysql",db="bag_data"):
        self.conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db)
        self.cursor = self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()
