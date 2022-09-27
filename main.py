import os
import dotenv
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from gb_parse.spiders.autoyoula import AutoyoulaSpider
from gb_parse.spiders.hhru import HhruSpider
from gb_parse.spiders.instagram import InstagramSpider
from gb_parse.spiders.instagram_users import InstagramUsersSpider
import logging


if __name__ == '__main__':
    dotenv.load_dotenv('../.env')
    users = ['lenochka_kuznecova_', 'fedor.kulish']
    crawl_settings = Settings()
    crawl_settings.setmodule(Settings)
    #logging.getLogger('scrapy').propagate = False

    crawl_proc = CrawlerProcess(settings=crawl_settings)
    #crawl_proc.crawl(AutoyoulaSpider)
    #crawl_proc.crawl(HhSpider)
    crawl_proc.crawl(InstagramSpider,
                  list_users=users,
                  login=os.getenv('INST_LOGIN'),
                  password=os.getenv('INST_PSWD'))
    crawl_proc.start()