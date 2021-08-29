# !/usr/bin/python3
# -*- coding: utf-8 -*
import pymysql
import psycopg2

import local_helpers


class DB:
    """class for working with DB"""

    def __init__(self, db_cfg):
        """Constructor"""
        self.db_cfg = db_cfg

    # подключение к базе
    def db_connector(self):
        db = pymysql.connect(self.db_cfg['db_host'], self.db_cfg['db_user'], self.db_cfg['db_pass'],
                             self.db_cfg['db_name'], charset='utf8mb4')
        cursor = db.cursor()
        return db, cursor

    # выполнение запроса
    def sql_execute(self, query):
        # local_helpers.Helpers.logger("TEST", "Test!")
        db, cursor = self.db_connector()
        # исполняем SQL-запрос
        try:
            cursor.execute(query)
            if "SELECT" in query or "UPDATE" in query:
                db.commit()
                db.close()
                res = [item[0] for item in cursor.fetchall()]
                return res
            db.commit()
            db.close()
        except pymysql.DatabaseError as err:
            local_helpers.Helpers.logger("DATABASE_ERROR", "ERROR_DESCR: " + str(err))
            db.close()
            return False


class DBPsql:

    def __init__(self, db_cfg):
        """Constructor"""
        self.db_cfg = db_cfg

    def db_connector(self):
        db = psycopg2.connect(dbname=self.db_cfg['db_name'], user=self.db_cfg['db_user'],
                              password=self.db_cfg['db_pass'], host=self.db_cfg['db_host'], port=self.db_cfg['db_port'])
        cursor = db.cursor()
        return db, cursor

    # выполнение запроса
    def sql_execute(self, query):
        db, cursor = self.db_connector()
        # исполняем SQL-запрос
        try:
            cursor.execute(query)
            if "SELECT" in query:
                db.commit()
                res = [item[0] for item in cursor.fetchall()]
                db.close()
                return res
            db.commit()
            db.close()
        except pymysql.DatabaseError as err:
            local_helpers.Helpers.logger("DATABASE_ERROR", "ERROR_DESCR: " + str(err))
            db.close()
            return False
