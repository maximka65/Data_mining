# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import os
import dotenv
import pymongo
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
from itemadapter import ItemAdapter



class YoulaParsePipeline:
    def process_item(self, item, spider):
        return item

class MongoSavePipeline:
    def __init__(self):
        self.db_client = pymongo.MongoClient(os.getenv('DATA_BASE'))
    def process_item(self, item, spider):
        db = self.db_client['data_mining_21_12_2020']
        collection = db[spider.name]
        collection.insert_one(item)
        return item

class GbImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for img_url in item.get("images", []):
            yield Request(img_url)

    def item_completed(self, results, item, info):
        item['images'] = [itm[1] for itm in results]
        return item

