# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
import dotenv
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
from pymongo import MongoClient

class GbParsePipeline:

    def __init__(self):
        dotenv.load_dotenv('../.env')
        #self.db = MongoClient(os.getenv('DATA_BASE'))['parser_i']

    def process_item(self, item, spider):
        #collection = self.db[spider.name]
        #collection.insert_one(item)
        return item

"""class GbImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        image = item.get('display_url')
        yield Request(image)
    def item_completed(self, results, item, info):
        item['display_url'] = results[0][1]
        return item"""