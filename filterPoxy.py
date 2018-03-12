#!/usr/local/Cellar/python3
# -*- coding: utf-8 -*-

import requests
import tool
import time

class filterPoxy(object):
    #===========================================================================
    # '''
    # 代理Ip有效性检查
    # writeLog: 写入运行记录到数据库, deleteData: 删除无效代理Ip, extractData: 提取代理Ip, start: 运行脚本
    # '''
    #===========================================================================
    def __init__(self):
        self.scriptName = "Ip有效性检查"
        self.operationDate = ''
        self.operatingTime = ''
        self.success = 0
        self.failure = 0
        self.repeat = 0
        self.crawlQuantity = 0
        self.my = tool.MYSQL()


    def writeLog(self):
        # 写入sql语句
        write_sql = """
        insert into scripting_log (script_name, operation_date, operating_time, crawl_quantity, success, failure, already) values (
        "{script_name}", "{operation_date}", "{operating_time}", "{crawl_quantity}", "{success}", "{failure}", "{already}")
        """

        # 插入日志信息
        self.my.executeOperation(write_sql.format(script_name=self.scriptName, operation_date=self.operationDate, operating_time=self.operatingTime,
                                                  crawl_quantity=self.crawlQuantity, success=self.success, failure=self.failure, already=self.repeat))


    def deleteData(self, ip, port):
        # 删除sql语句
        delete_sql = """delete from agent_pool where (ip="{ip}" and port="{port}")"""

        # 删除无效Ip
        self.my.executeOperation(delete_sql.format(ip=ip, port=port))


    def verification(self, poxyIp):
        status = True
        ip = poxyIp.split(":")[0]
        port = poxyIp.split(":")[1]

        # 检查链接
        filterUrl = 'https://httpbin.org/get?show_env=1'
        headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Mobile Safari/537.36'}

        try:
            # 使用代理Ip请求检测链接
            proxies = {
                "http": "http://" + poxyIp,
                "https": "http://" + poxyIp
            }
            r = requests.get(filterUrl, headers=headers, proxies=proxies, timeout=30)
            r.raise_for_status()

            # 记录可用数
            self.success += 1
        except Exception:
            # 记录不可用数
            self.failure += 1

            # 删除失败代理Ip信息
            self.deleteData(ip, port)

            status = False

        return status


    def extractData(self):
        # 查询sql语句
        inquire_sql = """SELECT ip, port from agent_pool """

        # 查询代理Ip库数据
        searchResult = self.my.queryOperation(inquire_sql)

        # 获取代理Ip总数
        self.crawlQuantity = len(searchResult)

        for info in searchResult:
            poxyIp = ("{ip}:{port}").format(ip=info[0], port=info[1])
            self.verification(poxyIp)

    def start(self):
        # 获取操作日期
        self.operationDate = time.strftime("%Y-%m-%d", time.localtime())

        # 获取操作时间
        self.operatingTime = time.strftime("%H:%M:%S", time.localtime())

        # 检测代理Ip库数据
        self.extractData()

        # 写入运行日志
        self.writeLog()


if __name__ == '__main__':
    examine = filterPoxy()
    examine.start()