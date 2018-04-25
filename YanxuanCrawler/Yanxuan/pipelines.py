# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql
import logging
import datetime
import json
import re
x=100
class YanxuanPipeline(object):

    def __init__(self):
        self.connect = pymysql.connect(
            host='localhost',
            port=3306,
            db='yanxuan',
            user='root',
            passwd='root',
            charset='utf8',
            use_unicode=True)
        # cursor = self.connect.cursor()

    def process_item(self, item, spider):
        emoji_pattern = re.compile('.\\ud83e.', flags=re.UNICODE)
        # emoji_pattern = re.compile('.\\[ud83e|ud83d|ud83c].', flags=re.UNICODE)

        cursor = self.connect.cursor()
        now = datetime.datetime.now()
        # attr_dict = escape_dict(item['attrs_dict'])
        # comments_dict = escape_dict(item['comments_dict'])

        # attrs_json = json.dumps(attr_dict) 
        # comments_json = json.dumps(comments_dict)
        comments_json = str(item['comments_dict'])
        comments_json=emoji_pattern.sub(r'XXX',comments_json)

        attrs_json = json.dumps(item['attrs_dict'])
        comments_json = json.dumps(comments_json)
        comments_tags = json.dumps(item['comments_tags'])

        attrs_json = pymysql.escape_string(attrs_json)
        comments_json = pymysql.escape_string(comments_json)
 
        comments_tags = pymysql.escape_string(comments_tags)
        # comments_tags = json.loads(comments_tags)
        # pymysql.converters.escape_str'

        
        sql="""CREATE TABLE goods_yanxuan (itemid int(8)NOT NULL primary key ,
                                             itemid_typeA int(8),
                                             itemid_typeB int(8),
                                             price decimal(7,2),
                                             comments_num int(5),
                                             say_good_pct decimal(3,2),
                                             seem_good_tag int(1),
                                             seem_cheap_tag int(1),
                                             updated datetime,
                                             comments_tags json,
                                             detail json , 
                                             comments mediumtext,
                                             id int(1))
                                             """


 
                                         

                                            
        sql_query = "SELECT 1 from goods_yanxuan where itemid = '%s'" %(int(item['itemId']))
        print(item['itemId'])
        sql_update = """UPDATE goods_yanxuan set itmeid = '%s' ,
                                         detail = '%s' ,
                                         comments = '%s' ,
                                         updated = '%s' ,
                                         itemid_typeA ='%s',
                                         itemid_typeB ='%s',
                                         price ='%s',
                                         comments_num ='%s',
                                         say_good_pct ='%s',
                                         seem_good_tag ='%s',
                                         seem_cheap_tag ='%s',
                                         comments_tags ='%s',
                                    where itmeId = '%d'
                    """% (
                        item['itemId'],
                        attrs_json,
                        comments_json,
                        now,
                        item['itemid_typeA']  ,
                        item['itemid_typeB'] ,
                        item['price'] ,
                        item['comments_num'],
                        item['say_good_pct'] ,
                        item['seem_good_tag'],
                        item['seem_cheap_tag'] ,
                        comments_tags,
                        int(item['itemId'])
                        )
        #这样不好，execute（sql，params）省心：自动拼接，自动转义）
        sql_insert = """insert into goods_yanxuan(updated,itemid,itemid_typeA,itemid_typeB,
                                                    price,comments_num,say_good_pct,seem_good_tag,
                                                    seem_cheap_tag,comments_tags,detail,comments )
                            values('%s', '%s', '%s','%s','%s', '%s', '%s','%s','%s', '%s', '%s','%s')
                    """% (now,item['itemId'],item['itemid_typeA'],item['itemid_typeB'],
                          item['price'],item['comments_num'],item['say_good_pct'],item['seem_good_tag'],
                          item['seem_cheap_tag'],comments_tags,attrs_json,comments_json
                        )       
                            
       
        cursor.execute('show tables')
        tables=cursor.fetchall()
        if  ('goods_yanxuan',) not in tables:
            try:
                cursor.execute(sql)
            except Exception as e:
              print("建表失败")
              raise e

        try:
            cursor.execute(sql_query)
            ret = cursor.fetchone()
            if ret:
                cursor.execute(sql_update)
                # print("成功更新一条数据!")
                print("pass 成功更新一条数据")
            else:
                try:
                    cursor.execute(sql_insert)
                    print("成功插入一条数据!")
                except Exception as e:
                    global x
                    print("继续debug吧")
                    f =  open('D:\数据科学\debug\jsontext\json'+str(x)+'.txt','w')
                    
                    f.write(str(sql_insert))
                    f.write('\n')
                    f.write(str(e))
                    f.write('\n')
                    f.write(item['itemId'])
                    # f.write(itme["itemID"])

                    x+=1
                    f.close()
            print('我在loc3')
            self.connect.commit()
            cursor.close() # 关闭连接

        except Exception as error:
            logging.warning(error)
        