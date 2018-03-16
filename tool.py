#!/usr/local/Cellar/python3
# -*- coding: utf-8 -*-

import pymysql
import configparser
import requests
import logging
import smtplib
from email.mime.text import MIMEText


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
    def __init__(self):
        self.proxyData = []
        self.quantity = 0
        self.my = MYSQL()


    def deleteData(self, ip, port):
        # 删除sql语句
        delete_sql = """delete from agent_pool where (ip="{ip}" and port="{port}")"""

        # 删除无效Ip
        self.my.executeOperation(delete_sql.format(ip=ip, port=port))

    def extractData(self):
        # 查询sql语句
        inquire_sql = """SELECT ip, port from agent_pool """

        # 查询获取代理Ip库数据
        self.proxyData = self.my.queryOperation(inquire_sql)

        # 获取代理Ip总数
        self.quantity = len(self.proxyData)


    def proxyGetHTMLText(self, url, code='utf-8'):
        self.extractData()
        html = ""

        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }

        for info in self.proxyData:
            ip = info[0]
            port = info[1]
            poxyIp = ("{ip}:{port}").format(ip=ip, port=port)

            proxies = {
                "http": "http://" + poxyIp,
                "https": "http://" + poxyIp
            }

            try:
                r = requests.get(url, headers=headers, proxies=proxies, timeout=20)
                status = r.status_code

                if status == 460:
                    # 删除失败代理Ip信息
                    self.deleteData(ip, port)
                    continue

                r.raise_for_status()
                r.encoding = code
                html = r.text
                break
            except Exception:
                logger = self.logger()
                logger.exception("Download HTML Text failed")
                # 删除失败代理Ip信息
                self.deleteData(ip, port)

        return html


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


class Mail(Log):
    #===========================================================================
    # '''
    # 各类邮件发送操作
    # agentExhaustedEmail: 代理Ip耗尽邮件
    # '''
    #===========================================================================
    def __init__(self):
        # 获取配置信息
        conf = configparser.ConfigParser()
        conf.read("/Users/wangjiacan/Desktop/sourceCode/configurationFile/localConfiguration.ini")

        self.account = conf.get("singleTimer", "account")
        self.password = conf.get("singleTimer", "password")
        self.recipient = conf.get("singleTimer", "recipient")


    def agentExhaustedEmail(self, scriptName):
        # 邮件内容
        content = "<font color=#000000><br>代理Ip已耗尽，请登录服务器手动抓取代理Ip。<br>运行失败脚本：{scriptName}</font>"
        # 邮件正文
        msg = MIMEText(content.format(scriptName=scriptName), 'html', 'utf-8')
        # 邮件标题
        msg["Subject"] = "代理Ip耗尽邮件"
        # 发件人
        msg["From"] = self.account
        # 收件人
        msg["To"] = self.recipient

        try:
            # 发送邮件
            server = smtplib.SMTP_SSL("smtp.qq.com", 465)
            server.login(self.account, self.password)
            server.sendmail(self.account, self.recipient, msg.as_string())
            server.quit()
        except Exception:
            # 记录错误日志
            logger = self.logger()
            logger.exception("Because the mail sending error can not be reminded to the developer, to stop the program running")

