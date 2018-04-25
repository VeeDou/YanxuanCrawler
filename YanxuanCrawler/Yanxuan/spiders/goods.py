 # -*- coding: utf-8 -*-
import scrapy
from bs4 import BeautifulSoup
import re
import json
import requests
from Yanxuan.items import YanxuanItem
from Yanxuan.settings import ITEM_IDED
import sys     #解决Non-BMP character无法存入数据库的问题。（一般来说是表情）
from copy import deepcopy #FOR COPY DICT
import time,io
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
tag = 1


sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')         

"""
1.过滤emoji（）
http://blog.csdn.net/ugg/article/details/44225723
http://blog.csdn.net/orangleliu/article/details/67632628?utm_source=gold_browser_extension
https://juejin.im/post/58cfd4a6570c350058ae6f7d

2.寻找对应兼容解码方式
https://www.zhihu.com/question/26921730
mysql
https://segmentfault.com/q/1010000000326270

mysql 用 utf8mb4编码就好了
emoji
http://www.oicqzone.com/qqjiqiao/2014123020663.html
"""

"""
1.取图片url
1.5 单独取商品id
2.写入mysql

3.新建 django项目，套用模板 
4.从数据库同步
5.简单力导向图实现
5.5带开关和图片的力导向图实现
6.从数据库取数据实现

"""
# emoji_pattern = re.compile(
#     u"(\ud83d[\ude00-\ude4f])|"  # emoticons
#     u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
#     u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
#     u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
#     u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
#     "+", flags=re.UNICODE)



class GoodsSpider(scrapy.Spider):

    name = 'goods'
    # allowed_domains = ['http://you.163.com/']
    # __timestamp=str(round(time.time()*1000))
    start_urls = ['http://you.163.com/xhr/globalinfo/queryTop.json']
    def parse(self, response):
        # response = TextResponse.text
 
        response = response.body
        print("response:"+str(response))

        id_mix= json.loads(response)

        # print(type(id_mix))
        #for output json
        json_out={}
        json_nodes=[]
        json_links=[]

        links=[]
        node_x=[{"id":"X","group":0}]
        json_out["nodes"] =node_x
        [
        {'name':
         'children':[]
        }
        ]
        for x in id_mix['data']['cateList']:
            link='http://you.163.com/item/list?categoryId='+str(x['id'])
            links.append(link)

            node_a={}
            node_a["id"]= x["id"]
            node_a["group"] = x["id"]
            json_nodes.append(node_a)

            #原点node x links
            link_x={}
            link_x["source"]=node_x[0]['id']
            link_x["target"]=node_a['id']
            link_x["value"]=1
            json_links.append(link_x)

            for y in x['subCateList']:
                node_b={}
                node_b["id"]= y["id"]
                node_b["group"] = x["id"]
                json_nodes.append(node_b)

                link_z={}
                link_z["source"]=node_a['id']
                link_z["target"]=node_b['id']
                link_z["value"]=1
                json_links.append(link_z)

            try:
                yield scrapy.Request(link,callback=self.parse_id)
            except Exception as e:
                print("type_A fail:"+str(e))
                continue

        #将json写入文件        
        json_out["nodes"].extend(json_nodes)
        json_out["links"]=json_links
 
        
        fp = open('D:\数据科学\django new\YanxuanViews\Visualization\static\json\json_out.json', 'w') 
        json.dump(json_out,fp)

        # f =  open("",'w')
        # f.write()
        # f.close()
        print('写入完成')

        print(links)


 
    def parse_id(self,response):
        html = response.body
        text = html.decode("utf-8")
        # print(html)
        print(len(text))
        id_t_list=re.findall(r'\[\],"id":\d*',text)
        ids=[]
        # ids_text = ""
        for idd_t in id_t_list:
            id_t = idd_t[8:]     ###20180302tag 什么逻辑
            ids.append(id_t)
        f = open("D:\数据科学\scrapy\Yanxuan0001\save4check\Text_cat\\"+str(response.url[-7:])+".txt",'w')
        f.write(response.url)
        f.write(str(text))
        f.write(str(ids))
        f.close()
        print("爬的这："+response.url)

        for idd in ids:
            if (int(idd),) not in ITEM_IDED:
                print("___________________get one___________________ ")
                good_url= 'http://you.163.com/item/detail?id='+idd
                yield scrapy.Request(good_url,callback=self.parse_good)
                
            else:
                print("pass one ")


    def parse_good(self,response):

        html = response.body
        # text = TextResponse.text
        text = html.decode("utf-8")
    #截取商品图片url
        text_left = text[text.find('listPicUrl')+13:]
        url_pic = text_left[:text_left.find('"')]
        itemId =  response.url[-7:]
        text_detail = text[text.find('appExclusiveFlag')-2:text.find('hdrkDetailVOList')-2].replace('\\n',' ').replace('\n',' ')+'}'
        attrs_dict = {}       # 属性字典（修）
    #3.9新增字段
        #关于评论
        comments_num = -1
        say_good_pct = -1   #好评比例 4星及以上的比例
        seem_good_tag = -1      #爆款标签，评论数999+
        comments_tags = {}  #评论标签们
        #关于详情
        seem_cheap_tag = -1  #打折标签
        itemid_typeA = 0    #大类ID
        itemid_typeB = 0    #小类ID
        price = 0

    #截取商品详情
        try:
            d_detail = json.loads(text_detail)
            #存入字段
            itemid_typeA = d_detail['categoryList'][0]['id']# 类别id（大类）
            itemid_typeB = d_detail['categoryList'][1]['id']# 类别id（小类）
            #存入字典
            name_type_a = d_detail['categoryList'][0]['name'] #类别名称（大类）
            name_type_b = d_detail['categoryList'][1]['name'] #类别名称（小类）
            counter_price = d_detail['counterPrice']            #柜台价 给 售价price 
            g_p = d_detail['gradientPrice']     #梯度价格

            if type(g_p)!=type(None):      #打折价格判断
                price = g_p['limitPrice']
                seem_cheap_tag = 1
            else:
                seem_cheap_tag = 0
                price = counter_price

            attr_list = d_detail['attrList']# 属性列表


        #汇总详情页信息
            
            for a_l in attr_list:
                attrs_dict[a_l["attrName"]] = a_l["attrValue"]

            attrs_dict["url_pic"] = url_pic
            attrs_dict["name_type_a"] = name_type_a
            attrs_dict["name_type_b"] = name_type_b
            attrs_dict["counter_price"] = counter_price

    ####################华丽丽的分割线################################

            # timestamp=''

        except Exception as e:
            # text_detail = text[text.find('appExclusiveFlag')-2:text.find('hdrkDetailVOList')-2].replace('\\n',' ').replace('\n',' ')+'}'
            # d_detail = json.loads(text_detail)
            # g_p = d_detail['gradientPrice']     #梯度价格
            # if type(g_p)!=type(None):      #打折价格判断
            #     price = g_p['limitPrice']
            # else:
            #     price = counter_price           
            # attrs_dict['url_pic']=url_pic
            # attrs_dict['price']= price

            print("detail解析出错了")
            f =  open("D:\数据科学\scrapy\Yanxuan0001\save4check\detail\detail"+str(itemId)+".txt",'w')
            f.write(response.url)
            f.write('\n')
            f.write('html:'+str(html)) 
            f.write('\n')
            f.write("text"+str(text))  
            f.write('\n')          
            f.write(str(text_detail))
            f.write('\n')
            f.write(str(e))
            f.close()
            raise e
 

    #解析评论 
        commnet_dict_list = [] #评论列表
        total_pages=0
        total_num=0

        dict_comment_pick={}
        comments_keys=["content","createTime","star","itemId",'frontUserName']
        try:
            page = 1
            url_comment = 'http://you.163.com/xhr/comment/listByItemByTag.json?&itemId='+str(itemId)+'&tag=%E5%85%A8%E9%83%A8&size=30&page='+str(page)
            url_tag_comment='http://you.163.com/xhr/comment/tags.json?itemId='+str(itemId)
            tag_comment = requests.get(url_tag_comment).text
            # comment = requests.get(url_comment).text.replace('\n',' ').translate(non_bmp_map)
            r = requests.get(url_comment)
            # r.encoding = r.apparent_encoding
            comment = r.text.replace('\n',' ').translate(non_bmp_map)
            #过滤emoji
            # comment=emoji_pattern.sub(r'XXX',comment)


            comments_tags = dict(json.loads(tag_comment))# code 和 data
            dict_comment = dict(json.loads(comment)) 

        #修整评论信息
            comments_dict={}       #汇总评论信息 评论列表+其它
            
            comments_num = dict_comment['data']['pagination']['total'] #评论总数
            if comments_num > 999:
                seem_good_tag=1
            else:
                seem_good_tag=0
 
            #筛选评论相关信息 pick
            print(1)
            dict_comment_pick = deepcopy(dict_comment['data']['result'])
            count_tag = 0
            # print(dict_comment_pick)
            ii=0
            try:
                for x in dict_comment['data']['result']:
                    for y in x:
                        if y  not in comments_keys:
                            # print("not in")
                            # print( dict_comment_pick[ii])
                            del dict_comment_pick[ii][y]
                            # print( dict_comment_pick[ii])
                        else:
                            if y == 'star' and dict_comment_pick[ii][y]>=4:
                                count_tag+=1
                            else:
                                pass
                    ii+=1
                
            except Exception as e:
                print(e) 
            # print("xxx"+str(dict_comment_pick))    
            print(3)

            commnet_dict_list.append(dict_comment_pick)
            print(4)
            # print('dict_comment_pick:'+str(dict_comment_pick))
            print(5)
            total_pages = dict_comment['data']['pagination']['totalPage'] 
            print(6)
            if total_pages > 1:
                print(7)
                for p in range(2,total_pages+1):
                    page = p
                    url_comment = 'http://you.163.com/xhr/comment/listByItemByTag.json?&itemId='+str(itemId)+'&tag=%E5%85%A8%E9%83%A8&size=30&page='+str(page)
                    # print("我在这里！："+url_comment)
                    # comment = requests.get(url_comment).text.translate(non_bmp_map)
                    r1 = requests.get(url_comment)
                    # r1.encoding = r1.apparent_encoding
                    comment = r1.text.replace('\n',' ').translate(non_bmp_map)
                    #过滤emoji
                    # comment=emoji_pattern.sub(r'XXX',comment)
                    
                    dict_comment = dict(json.loads(comment))
                    dict_comment_pick = deepcopy(dict_comment['data']['result'])
                    ii=0
                    try:
                        for x in dict_comment['data']['result']:
                            for y in x:
                                if y  not in comments_keys:
                                    # print("not in")
                                    # print( dict_comment_pick[ii])
                                    del dict_comment_pick[ii][y]
                                    # print( dict_comment_pick[ii])
                                else:
                                    if y == 'star' and dict_comment_pick[ii][y]>=4:
                                        count_tag+=1
                                    else:
                                        pass
                            ii+=1
                            # print(ii)
                    except Exception as e:
                        print(e) 
                    # print("xxx"+str(dict_comment_pick))    
                    commnet_dict_list.append(dict_comment_pick)
                #say_good_pct
            try:
                say_good_pct = count_tag/comments_num
                say_good_pct = round(say_good_pct,3)
                print('say_good_pct:'+str(say_good_pct))
                print('count_tag:'+str(count_tag))
                print('comments_num:'+str(comments_num))
            except Exception as e:
                say_good_pct = 0
                        
        except Exception as e:    
            f =  open("D:\数据科学\scrapy\Yanxuan0001\save4check\comments\comments"+str(itemId)+".txt",'w')
            f.write(response.url)
            f.write('\n')
            f.write(str(e))
            f.close()
###########
    #汇总评论信息
        # print('commnet_dict_list:'+str(commnet_dict_list))
        comments_dict['comments'] =  commnet_dict_list
        comments_dict['total_pages'] = total_pages





    #存入item
        item = YanxuanItem()
        item['comments_dict'] = comments_dict
        item['attrs_dict'] = attrs_dict
        item['itemId'] = itemId
        item['comments_num'] = comments_num
        item['comments_tags'] = comments_tags

        item['say_good_pct'] = say_good_pct
        item['seem_good_tag'] = seem_good_tag
        item['seem_cheap_tag'] = seem_cheap_tag
        item['itemid_typeA'] = itemid_typeA
        item['itemid_typeB'] = itemid_typeB
        item['price'] = price

        yield item    

         


