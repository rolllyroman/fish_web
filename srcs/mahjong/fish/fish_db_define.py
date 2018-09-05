#coding:utf-8

import pymysql

class Mysql_instance(object):
    def __init__(self,host="127.0.0.1",port=3306,user="root",passwd="168mysql",db="fish_data"):
        self.conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db)
        self.cursor = self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()
