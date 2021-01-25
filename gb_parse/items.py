# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class YoulaParseItem(scrapy.Item):
    _id = scrapy.Field()
    title = scrapy.Field()
    images = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    author = scrapy.Field()
    specifications = scrapy.Field()
    price = scrapy.Field()
    test = scrapy.Field()

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