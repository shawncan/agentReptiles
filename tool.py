#!/usr/local/Cellar/python3
# -*- coding: utf-8 -*-

import pymysql
import configparser
import requests
import logging


class Log(object):
    #===========================================================================
    # '''
    # 日志操作
    # logger: 建立日志
    # '''
    #===========================================================================
    def logger(self):
        logging.basicConfig(level=logging.WARNING,
                            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename='/Users/wangjiacan/Desktop/sourceCode/log/agentReptiles.txt',
                            filemode='a')

        logger = logging.getLogger()

        return logger

class MYSQL(object):
    #===========================================================================
    # '''
    # 数据库操作
    # getCursor: 数据库连接, queryOperation: 查询数据库, executeOperation: 写入数据库
    # '''
    #===========================================================================
    def __init__(self):
        conf = configparser.ConfigParser()
        conf.read("/Users/wangjiacan/Desktop/sourceCode/configurationFile/localConfiguration.ini")

        self.host = conf.get("localServer", "host")
        self.port = int(conf.get("localServer", "port"))
        self.user = conf.get("localServer", "user")
        self.password = conf.get("localServer", "password")
        self.dbName = conf.get("localServer", "dbname")

    def getCursor(self):
        # 建立数据库链接
        self.db = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password, db=self.dbName, charset='utf8')

        # 创建游标对象
        cursor = self.db.cursor()

        # 返回游标对象
        return cursor

    def queryOperation(self,sql):
        # 建立连接获取游标对象
        cur = self.getCursor()

        # 执行SQL语句
        cur.execute(sql)

        # 获取查询数据
        # fetch*
        # all 所有数据, one 取结果的一行, many(size),去size行
        dataList = cur.fetchall()

        # 关闭游标
        cur.close()

        # 关闭数据库连接
        self.db.close()

        # 返回查询数据
        return dataList

    def executeOperation(self,sql):
        # 操作状态
        operatingStatus = 0

        # 建立连接获取游标对象
        cur = self.getCursor()

        try:
            # 执行SQL语句
            cur.execute(sql)

            # 提交修改
            self.db.commit()
        except Exception as error:
            print(error)

            # 错误回滚
            self.db.rollback()

            # 更改操作状态
            operatingStatus = 1

        # 关闭游标
        cur.close()

        # 关闭数据库连接
        self.db.close()

        return operatingStatus


class WebDownload(Log):
    #===========================================================================
    # '''
    # 网页下载操作
    # getHTMLText: 下载网页源码
    # '''
    #===========================================================================
    def getHTMLText(self, url, code='utf-8'):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }

        try:
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()
            r.encoding = code
            print(r.status_code)
            return r.text
        except Exception:
            logger = self.logger()
            logger.exception("Download HTML Text failed")

