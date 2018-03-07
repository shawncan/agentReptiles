#!/usr/local/Cellar/python3
# -*- coding: utf-8 -*-

import re
from bs4 import BeautifulSoup
import time
import tool

class xicidaili(object):
    #===========================================================================
    # '''
    # 西刺代理网站免费ip爬取
    # writeLog: 写入运行记录到数据库
    # writeIP: 写入代理Ip到数据库
    # extractIp: 提取网页代码中的代理Ip
    # start: 运行脚本
    # '''
    #===========================================================================
    def __init__(self):
        self.scriptName = "西刺代理"
        self.aimsUrlList = ['http://www.xicidaili.com/nn/', 'http://www.xicidaili.com/nt/', 'http://www.xicidaili.com/wn/', 'http://www.xicidaili.com/wt/']
        self.proxyList = []
        self.download = tool.WebDownload()
        self.my = tool.MYSQL()
        self.success = 0
        self.failure = 0
        self.repeat = 0
        self.crawlQuantity = 0
        self.operatingTime = ''


    def writeLog(self):
        # 写入sql语句
        write_sql = """
        insert into scripting_log (script_name, operating_time, crawl_quantity, success, failure, already) values (
        "{script_name}", "{operating_time}", "{crawl_quantity}", "{success}", "{failure}", "{already}")
        """

        # 插入日志信息
        self.my.executeOperation(write_sql.format(script_name=self.scriptName, operating_time=self.operatingTime,
                                                  crawl_quantity=self.crawlQuantity, success=self.success, failure=self.failure, already=self.repeat))


    def writeIP(self):
        # 写入sql语句
        write_sql = """
        insert into agent_pool (ip, port, type, verification_time) VALUES ("{ip}", "{port}", "{ipType}", "{verificationTime}")
        """
        # 查询sql语句
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
                writeState = self.my.executeOperation(write_sql.format(ip=ip, port=port, ipType=ipType, verificationTime=verificationTime))

                # 记录插入情况
                if writeState == 0:
                    self.success += 1
                else:
                    self.failure += 1
            else:
                self.repeat += 1
                continue


    def extractIp(self, url):
        # 获取开始小时与结束小时
        endHour = int(time.strftime("%H", time.localtime()))
        startHour = endHour - 2

        # 获取源码并解析
        html = self.download.getHTMLText(url)
        soup = BeautifulSoup(html, 'html.parser')

        # 提取table标签下内容
        table = soup.find('table')
        # 提取tr标签下内容，信息所在标签
        tr = table.find_all('tr')

        for info in tr[1:]:
            proxyData = {'ip': '', '端口': '', '类型': '', '验证时间': '', }

            # 获取td标签下内容
            trContent = re.findall(r'<td>.*</td>', str(info))

            # 获取验证时间
            verificationTime = trContent[4][4:-5]
            # 获取验证的小时
            hour = int(verificationTime.split(" ")[1].split(":")[0])
            # 当前小时小于等于开始小时的跳过
            if hour <= startHour :
                continue
            # 当前小时大于等于结束小时的跳过
            if hour >= endHour :
                continue

            # 获取bar所属div标签下的内容
            filterContent = re.findall(r'<div class="bar" .*>', str(info))
            # 获取连接速度
            speed = filterContent[0].split('"')[3][:-1]
            # 获取连接时间
            connect_time = filterContent[1].split('"')[3][:-1]
            # 判断连接速度大于3秒跳过
            if float(speed) > 3:
                continue
            # 判断连接时间大于1秒跳过
            if float(connect_time) > 1:
                continue

            # ip地址
            ip = trContent[0][4:-5]
            # 端口
            port = trContent[1][4:-5]
            # 类型
            ipType = trContent[2][4:-5]

            proxyData['ip'] = ip
            proxyData['端口'] = port
            proxyData['类型'] = ipType
            proxyData['验证时间'] = verificationTime

            # 添加代理字典到代理列表中
            self.proxyList.append(proxyData)

            # 记录爬取成功数
            self.crawlQuantity += 1


    def start(self):
        # 获取操作时间
        self.operatingTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        for url in self.aimsUrlList:
            self.extractIp(url)
        self.writeIP()

        # 写入运行日志
        self.writeLog()


if __name__ == '__main__':
    extract = xicidaili()
    extract.start()
