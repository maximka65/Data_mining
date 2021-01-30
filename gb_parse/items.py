# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import time
from itemloaders.processors import MapCompose, Join


class GbParseItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class HhVacancyItem(scrapy.Item):
    _id = scrapy.Field()
    vacancy_url = scrapy.Field()
    title = scrapy.Field()
    salary = scrapy.Field()
    description = scrapy.Field()
    skills = scrapy.Field()
    company_url = scrapy.Field()

class HhCompanyItem(scrapy.Item):
    _id = scrapy.Field()
    company_url = scrapy.Field()
    company_name = scrapy.Field()
    company_site = scrapy.Field()
    prof_area = scrapy.Field()
    company_description = scrapy.Field()

class InstagramHashtagItem(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    hashtag_id = scrapy.Field()
    hashtag_name = scrapy.Field()
    hashtag_image = scrapy.Field()

class InstagramHashtagMediaItem(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    date_create = scrapy.Field(
        input_processor=MapCompose(lambda t: time.ctime(t))
    )
    node_id = scrapy.Field()
    node_owner = scrapy.Field()
    display_url = scrapy.Field()

class InstagramUsersItem(scrapy.Item):
    _id = scrapy.Field()
    edge_followed_by = scrapy.Field()
    edge_follow = scrapy.Field()