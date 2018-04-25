# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class YanxuanItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    attrs_dict = scrapy.Field()
    comments_dict = scrapy.Field() 
    itemId = scrapy.Field()

    comments_num = scrapy.Field()
    comments_tags = scrapy.Field()  #评论标签们 
    say_good_pct = scrapy.Field() #好评比例 4星及以上的比例
    seem_good_tag = scrapy.Field()  #爆款标签，评论数999+
    seem_cheap_tag = scrapy.Field()  #打折标签


    itemid_typeA = scrapy.Field() #大类ID
    itemid_typeB = scrapy.Field() #小类ID
    price = scrapy.Field()    