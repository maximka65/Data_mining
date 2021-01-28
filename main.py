import os
import dotenv
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from gb_parse.spiders.autoyoula import AutoyoulaSpider
from gb_parse.spiders.hhru import HhruSpider
from gb_parse.spiders.instagram import InstagramSpider


if __name__ == '__main__':
    dotenv.load_dotenv('../.env')
    hash_tags = ['qwertyrc', 'qwertart']
    tasks = []
    crawler_settings = Settings()
    crawler_settings.setmodule('gb_parse.settings')
    crawler_process = CrawlerProcess(settings=crawler_settings)
    #crawler_process.crawl(AutoyoulaSpider)
    #crawler_process.crawl(HhruSpider)
    crawler_process.crawl(InstagramSpider,
                     start_hash_tags=hash_tags,
                     login=os.getenv('INST_LOGIN'),
                     password=os.getenv('INST_PSWD'))
    crawler_process.start()



