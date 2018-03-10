#!/usr/local/Cellar/python3
# -*- coding: utf-8 -*-

import smtplib
from email.mime.text import MIMEText
import configparser
import tool
import datetime


class healthMail(object):
    #===========================================================================
    # '''
    # 脚本运行情况统计邮件脚本
    # obtainLog: 获取昨日运行数据, deleteData: 删除无效代理Ip, extractData: 提取代理Ip, start: 运行脚本
    # '''
    #===========================================================================
    def __init__(self):
        self.account = ''
        self.password = ''
        self.recipient = ''
        self.yesterday = ''
        self.scriptingLogRowList = []
        self.crawlingStatisticsRowList = []
        self.my = tool.MYSQL()


    def scriptStatistics(self):
        # 查询运行脚本名称sql语句
        scriptName_sql = """
        select distinct(script_name) from scripting_log where operation_date = "{yesterday}"
        """

        # 查询脚本单日总爬取数sql语句
        crawlQuantity_sql = """
        select sum(crawl_quantity) from `scripting_log`  where script_name="{scriptName}" and operation_date = "{yesterday}"
        """

        # 查询脚本单日总入库成功数sql语句
        success_sql = """
        select sum(success) from `scripting_log`  where script_name="{scriptName}" and operation_date = "{yesterday}"
        """

        # 查询脚本单日总入库失败数sql语句
        failure_sql = """
        select sum(failure) from `scripting_log`  where script_name="{scriptName}" and operation_date = "{yesterday}"
        """

        # 查询脚本单日总重复数sql语句
        already_sql = """
        select sum(already) from `scripting_log`  where script_name="{scriptName}" and operation_date = "{yesterday}"
        """

        # 爬取统计行代码
        row = """
        <tr>
            <td align="center">{scriptName}</td>
            <td align="center">{crawlQuantity}</td>
            <td align="center">{success}</td>
            <td align="center">{failure}</td>
            <td align="center">{already}</td>
        </tr>
        """
        # 运行脚本名称列表
        scriptNameList = []

        # 获取昨日运行脚本名称
        scriptNameData = self.my.queryOperation(scriptName_sql.format(yesterday=self.yesterday))

        # 循环提取脚本名称
        for info in scriptNameData:
            scriptNameList.append(info[0])

        # 循环提取脚本的统计数据
        for scriptName in scriptNameList:
            crawlQuantity = int((self.my.queryOperation(crawlQuantity_sql.format(scriptName=scriptName, yesterday=self.yesterday)))[0][0])
            success = int((self.my.queryOperation(success_sql.format(scriptName=scriptName, yesterday=self.yesterday)))[0][0])
            failure = int((self.my.queryOperation(failure_sql.format(scriptName=scriptName, yesterday=self.yesterday)))[0][0])
            already = int((self.my.queryOperation(already_sql.format(scriptName=scriptName, yesterday=self.yesterday)))[0][0])

            # 组合脚本统计行代码
            crawlingStatistics = row.format(scriptName=scriptName, crawlQuantity=crawlQuantity, success=success, failure=failure, already=already)

            # 添加脚本统计行代码列表
            self.crawlingStatisticsRowList.append(crawlingStatistics)


    def obtainLog(self):
        # 查询运行记录sql语句
        inquire_sql = """
        select script_name, operating_time, crawl_quantity, success, failure, already from scripting_log where operation_date = "{yesterday}"
        """

        # 运行记录行代码
        row = """
        <tr>
            <td align="center">{scriptName}</td>
            <td align="center">{operatingTime}</td>
            <td align="center">{crawlQuantity}</td>
            <td align="center">{success}</td>
            <td align="center">{failure}</td>
            <td align="center">{repeat}</td>
        </tr>
        """

        # 获取昨天数据
        searchResult = self.my.queryOperation(inquire_sql.format(yesterday=self.yesterday))

        # 提取数据信息
        for info in searchResult:
            scriptName = info[0]
            operatingTime = info[1]
            crawlQuantity = info[2]
            success = info[3]
            failure = info[4]
            repeat = info[5]

            # 组合爬取记录行代码
            scriptingLog = row.format(scriptName=scriptName, operatingTime=operatingTime, crawlQuantity=crawlQuantity,
                                     success=success, failure=failure, repeat=repeat)

            # 添加爬取记录行代码列表
            self.scriptingLogRowList.append(scriptingLog)


    def mail(self):
        # 表格代码
        recordForm = """
        <html>
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <body>
        <div>
            <div>
                <table border="2" bordercolor="black" cellspacing="2">
                    <tr>
                        <td align="center" width="520" height="35" colspan="5"><strong>代理Ip脚本爬取统计</strong></td>
                    </tr>
                    <tr>
                        <td align="center" width="120" height="25"><strong>爬取站点</strong></td>
                        <td align="center" width="100" height="25"><strong>爬取数据</strong></td>
                        <td align="center" width="100" height="25"><strong>入库成功</strong></td>
                        <td align="center" width="100" height="25"><strong>入库失败</strong></td>
                        <td align="center" width="100" height="25"><strong>入库重复</strong></td>
                    </tr>
                    {crawlingStatisticsRow}
                </table>
                <br />
                <br />
                <table border="2" bordercolor="black" cellspacing="2">
                    <tr>
                        <td align="center" width="700" height="35" colspan="6"><strong>代理Ip爬取脚本运行记录</strong></td>
                    </tr>
                    <tr>
                        <td align="center" width="120" height="25"><strong>爬取站点</strong></td>
                        <td align="center" width="180" height="25"><strong>操作时间</strong></td>
                        <td align="center" width="100" height="25"><strong>爬取数据</strong></td>
                        <td align="center" width="100" height="25"><strong>入库成功</strong></td>
                        <td align="center" width="100" height="25"><strong>入库失败</strong></td>
                        <td align="center" width="100" height="25"><strong>入库重复</strong></td>
                    </tr>
                    {scriptingLogRow}
                </table>
            </div>
        </div>
        </body>
        </html>
        """
        # 总统计记录行代码
        crawlingStatisticsRow = ''

        # 总运行记录行代码
        scriptingLogRow = ''

        # 组合所有统计记录的行代码
        for crawlingStatistics in self.crawlingStatisticsRowList:
            crawlingStatisticsRow += crawlingStatistics

        # 组合所有运行记录的行代码
        for scriptingLog in self.scriptingLogRowList:
            scriptingLogRow += scriptingLog

        # 邮件正文
        msg = MIMEText((recordForm.format(crawlingStatisticsRow=crawlingStatisticsRow, scriptingLogRow=scriptingLogRow)), 'html', 'utf-8')
        # 邮件标题
        msg["Subject"] = "{yesterday}脚本运行情况统计".format(yesterday=self.yesterday)
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
        except:
            # 邮件发送失败打印
            print("Because the mail sending error can not be reminded to the developer, to stop the program running")


    def start(self):
        # 获取昨天日期
        # datetime.datetime.now(): 获取当前日期, datetime.timedelta(days=-1): 设置时间差值1天, strftime('%Y-%m-%d'): 格式化时间
        self.yesterday = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')

        # 获取配置信息
        conf = configparser.ConfigParser()
        conf.read("/Users/wangjiacan/Desktop/sourceCode/configurationFile/localConfiguration.ini")

        self.account = conf.get("singleTimer", "account")
        self.password = conf.get("singleTimer", "password")
        self.recipient = conf.get("singleTimer", "recipient")

        # 获取昨天脚本统计数据
        self.scriptStatistics()

        # 获取昨天脚本运行数据
        self.obtainLog()

        # 发送昨天脚本运行记录
        self.mail()


if __name__ == '__main__':
    mail = healthMail()
    mail.start()