#!/usr/local/Cellar/python3
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import time
import tool
import filterPoxy
import os
import sys


class kuaidaili(object):
    #===========================================================================
    # '''
    # 快代理免费ip爬取
    # writeLog: 写入运行记录到数据库, writeIP: 写入代理Ip到数据库, extractIp: 提取网页代码中的代理Ip, start: 运行脚本
    # '''
    #===========================================================================
    def __init__(self):
        self.scriptName = "快代理"
        self.aimsUrl ='https://www.kuaidaili.com/free/inha/1/'
        self.proxyList = []
        self.success = 0
        self.failure = 0
        self.repeat = 0
        self.crawlQuantity = 0
        self.operationDate = ''
        self.operatingTime = ''
        self.download = tool.WebDownload()
        self.my = tool.MYSQL()
        self.mail = tool.Mail()
        self.examine = filterPoxy.filterPoxy()


    def writeLog(self):
        # 插入日志sql语句
        write_sql = """
        insert into scripting_log (script_name, operation_date, operating_time, crawl_quantity, success, failure, already) values (
        "{script_name}", "{operation_date}", "{operating_time}", "{crawl_quantity}", "{success}", "{failure}", "{already}")
        """

        # 插入日志信息
        self.my.executeOperation(write_sql.format(script_name=self.scriptName, operation_date=self.operationDate, operating_time=self.operatingTime,
                                                  crawl_quantity=self.crawlQuantity, success=self.success, failure=self.failure, already=self.repeat))


    def writeIP(self):
        # 写入代理sql语句
        write_sql = """
        insert into agent_pool (ip, port, type, verification_time) VALUES ("{ip}", "{port}", "{ipType}", "{verificationTime}")
        """
        # 查询代理sql语句
        inquire_sql = """
        select * from agent_pool WHERE ip = "{ip}" and port = "{port}"
        """

        # 循环插入ip数据
        for infoData in self.proxyList:
            # 提取每个字典数据
            ip = infoData["ip"]
            port = infoData["端口"]
            ipType = infoData["类型"]
            verificationTime = infoData["验证时间"]

            # 查询是否已存在ip信息
            searchResult = self.my.queryOperation(inquire_sql.format(ip=ip, port=port))

            # 插入ip信息
            if not searchResult:
                self.my.executeOperation(write_sql.format(ip=ip, port=port, ipType=ipType, verificationTime=verificationTime))
            else:
                self.repeat += 1
                continue


    def extractIp(self, url):
        # 获取开始小时与结束小时
        endHour = int(time.strftime("%H", time.localtime()))
        startHour = endHour - 2

        # 获取源码并解析
        html = self.download.proxyGetHTMLText(url)

        # 处理处理源码为0的情况
        if not html :
            scriptName = os.path.basename(__file__)
            self.mail.agentExhaustedEmail(scriptName)
            sys.exit(0)

        soup = BeautifulSoup(html, 'html.parser')

        # 提取table标签下内容
        table = soup.find('table', attrs={'class': 'table table-bordered table-striped'})
        # 提取tr标签下内容
        ipList = table.find_all('td', attrs={'data-title':'IP'})
        portList = table.find_all('td', attrs={'data-title': 'PORT'})
        timeList = table.find_all('td', attrs={'data-title': '最后验证时间'})

        for num in range(len(ipList)):
            # 代理字典
            proxyData = {'ip': '', '端口': '', '类型': '', '验证时间': '', }

            # 时间
            verificationTime = timeList[num].text
            hour = int(verificationTime[11:-6])

            # 当前小时小于等于开始小时的跳过
            if hour <= startHour :
                continue
            # 当前小时大于等于结束小时的跳过
            if hour >= endHour :
                continue

            # 记录爬取数
            self.crawlQuantity += 1

            # 获取ip
            ip = ipList[num].text
            # 获取端口
            port = portList[num].text

            # 组合ip与端口
            poxyIp = ("{ip}:{port}").format(ip=ip, port=port)
            # 验证ip是否可用
            ipStatus = self.examine.verification(poxyIp)

            # 判断是否可用
            # 可用: 添加ip信息至代理字典, 不可用: 跳过此循环
            if ipStatus:
                # 记录可用数
                self.success += 1
            else:
                # 记录不可用数
                self.failure += 1
                continue

            # 添加至代理字典
            proxyData['ip'] = ip
            proxyData['端口'] = port
            proxyData['类型'] = "HTTP"
            proxyData['验证时间'] = verificationTime

            # 添加代理字典到代理列表中
            self.proxyList.append(proxyData)


    def start(self):
        # 获取操作日期
        self.operationDate = time.strftime("%Y-%m-%d", time.localtime())

        # 获取操作时间
        self.operatingTime = time.strftime("%H:%M:%S", time.localtime())

        # 爬取ip
        self.extractIp(self.aimsUrl)

        # 写入ip
        self.writeIP()

        # 写入运行日志
        self.writeLog()


if __name__ == '__main__':
    extract = kuaidaili()
    extract.start()
