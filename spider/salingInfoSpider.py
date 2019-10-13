# -*- coding: utf-8 -*-
import random
import re
import requests
import sys
import lxml

from bs4 import BeautifulSoup
from generate_excle import generate_excle
from AgentAndProxies import hds
from AgentAndProxies import GetIpProxy
from model.ElementConstant import ElementConstant

defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)


class salingInfo:
    # 初始化构造函数
    def __init__(self):
        self.elementConstant = ElementConstant()
        self.getIpProxy = GetIpProxy()
        self.url = "https://bj.lianjia.com/ershoufang/pg{}/"
#        self.url = "https://bj.lianjia.com/chengjiao/pg{}/"
        self.infos = {}
        self.proxyServer = ()
        # 传参使用进行excle生成
        self.generate_excle = generate_excle()
        self.elementConstant = ElementConstant()

    # 生成需要生成页数的链接
    def generate_allurl(self, user_in_nub):
        for url_next in range(1, int(user_in_nub) + 1):
            self.page = url_next
            yield self.url.format(url_next)

    # 开始函数
    def start(self):
        self.generate_excle.addSheetExcle(u'在售列表')
        user_in_nub = input('输入生成页数：')

        for i in self.generate_allurl(user_in_nub):
            try:
                self.get_allurl(i)
                print(i)
            except Exception, e:
                print(e)
                print(i, 'failed')
        self.generate_excle.saveExcle('LianJiaSpider.xls')

    def get_allurl(self, generate_allurl):
        geturl = self.requestUrlForRe(generate_allurl)
        print geturl.status_code
        if geturl.status_code == 200:
            # 提取title跳转地址　对应每个商品
            re_set = re.compile('<div.*?class="item".*?data-houseid.*?<a.*?class="img.*?".*?href="(.*?)"')
            re_get = re.findall(re_set, geturl.text)
            for index in range(len(re_get)):
                print re_get[index] 
                self.open_url(re_get[index], index)

    def open_url(self, re_get, index):
        res = self.requestUrlForRe(re_get)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'lxml')
            self.infos['网址'] = re_get
            self.infos['标题'] = soup.select('.main')[0].text
            self.infos['总价'] = soup.select('.total')[0].text + u'万'
            self.infos['每平方售价'] = soup.select('.unitPriceValue')[0].text

            self.infos['户型'] = soup.select('.mainInfo')[0].text
            self.infos['朝向'] = soup.select('.mainInfo')[1].text
            self.infos['大小'] = soup.select('.mainInfo')[2].text
            self.infos['楼层'] = soup.select('.subInfo')[0].text
            self.infos['装修'] = soup.select('.subInfo')[1].text
            self.infos['房子类型'] = soup.select('.subInfo')[2].text

            self.infos['小区名称'] = soup.select('.info')[0].text
            self.infos['区域'] = soup.select('.info > a')[0].text
            # infos['地区'] = soup.select('.info > a')[1].text
            self.infos['详细区域'] = soup.select('.info')[1].text
            self.infos['链家编号'] = soup.select('.info')[3].text
            self.infos['关注房源'] = soup.select('#favCount')[0].text + u"人关注"
            self.infos['看过房源'] = soup.select('#cartCount')[0].text + u"人看过"

            partent = re.compile('<li><span class="label">(.*?)</span>(.*?)</li>')
            result = re.findall(partent, res.text)

            for item in result:
                if item[0] != u"抵押信息" and item[0] != u"房本备件":
                    self.infos[item[0]] = item[1]
            row = index + (self.page - 1) * 30
            self.infos['序号'] = row + 1
            self.infos['状态'] = u'在售'
            self.infos['城市'] = u'北京'
            print 'row:' + str(row)
            if row == 0:
                for index_item in self.elementConstant.data_constant.keys():
                    self.generate_excle.writeExclePositon(0, self.elementConstant.data_constant.get(index_item),
                                                          index_item)

                self.wirte_source_data(1)

            else:
                row = row + 1
                self.wirte_source_data(row)
        return self.infos

    # 封装统一request请求,采取动态代理和动态修改User-Agent方式进行访问设置,减少服务端手动暂停的问题
    def requestUrlForRe(self, url):

        try:
            if len(self.proxyServer) == 0:
                tempProxyServer = self.getIpProxy.get_random_ip()
            else:
                tempProxyServer = self.proxyServer

            proxy_dict = {
                tempProxyServer[0]: tempProxyServer[1]
            }
            tempUrl = requests.get(url, headers=hds[random.randint(0, len(hds) - 1)], proxies=proxy_dict)

            code = tempUrl.status_code
            if code >= 200 or code < 300:
                self.proxyServer = tempProxyServer
                return tempUrl
            else:
                self.proxyServer = self.getIpProxy.get_random_ip()
                return self.requestUrlForRe(url)
        except Exception as e:
            self.proxyServer = self.getIpProxy.get_random_ip()
            s = requests.session()
            s.keep_alive = False
            return self.requestUrlForRe(url)

    # 源数据生成,写入excle中,从infos字典中读取数据,放置到list列表中进行写入操作,其中可修改规定写入格式
    def wirte_source_data(self, row):
        for itemKey in self.infos.keys():
            print itemKey + ':' + str(self.infos.get(itemKey))

            item_valus = self.infos.get(itemKey)
            if itemKey == '详细区域':
                temps_item_valus = item_valus.split()
                print temps_item_valus[0], temps_item_valus[1], temps_item_valus[2]
                self.generate_excle.writeExclePositon(row, self.elementConstant.data_constant.get('所属下辖区'),
                                                      temps_item_valus[0])
                self.generate_excle.writeExclePositon(row, self.elementConstant.data_constant.get('所属商圈'),
                                                      temps_item_valus[1])
                self.generate_excle.writeExclePositon(row, self.elementConstant.data_constant.get('所属环线'),
                                                      temps_item_valus[2])
            else:

                tempItemKey = self.elementConstant.unit_check_name(itemKey.encode('utf-8'))
                count = self.elementConstant.data_constant.get(tempItemKey)
                print tempItemKey, self.elementConstant.data_constant.get(tempItemKey), item_valus
                if tempItemKey != None and count != None:
                    # todo 检查使用标准,修改使用逻辑
                    if tempItemKey == '链家编号':
                        item_valus = item_valus[0:len(item_valus) - 2]
                    elif tempItemKey == '单价（元/平米）':
                        item_valus = item_valus[0:len(item_valus) - 4]
                    elif tempItemKey == '建筑面积：平米':
                        item_valus = item_valus[0:len(item_valus) - 1]
                    elif tempItemKey == '建成时间：年':
                        item_valus = item_valus[0:item_valus.index('年')]
                    elif tempItemKey == '关注（人）' or tempItemKey == '看过房源：人':
                        item_valus = item_valus[0:len(item_valus) - 3]
                    elif tempItemKey == '挂牌时间':
                        item_valus = item_valus.replace('-', '/')
                    elif tempItemKey == '上次交易时间':
                        item_valus = item_valus.replace('-', '/')

                    self.generate_excle.writeExclePositon(row,
                                                          self.elementConstant.data_constant.get(tempItemKey),
                                                          item_valus)


spider = salingInfo()
spider.start()
