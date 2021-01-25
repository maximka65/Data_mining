import scrapy
from urllib.parse import urljoin
from pymongo import MongoClient
from ..loaders import YoulaParseItem


class AutoyoulaSpider(scrapy.Spider):
    name = "autoyoula"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]
    db = MongoClient(
        'mongodb+srv://maximka:78301574@cluster0.9thha.mongodb.net/autoyoula?retryWrites=true&w=majority'
    )['autoyoula']
    collection = db['coll1']

    xpath_query = {
        'brands': "//div[@class='TransportMainFilters_brandsList__2tIkv']//a[@data-target='brand']/@href",
        "pagination": "//div[contains(@class, 'Paginator_block')]/a[contains(@class, 'Paginator_button')]/@href",
        "ads": '//article[contains(@data-target, "serp-snippet")]//a[@data-target="serp-snippet-title"]/@href'
    }

    itm_template = {
        "title": '//div[@data-target="advert-title"]/text()',
        "images": '//figure[contains(@class, "PhotoGallery_photo")]//img/@src',
        "description": '//div[contains(@class, "AdvertCard_descriptionInner")]//text()',
        "author": '//script[contains(text(), "window.transitState =")]/text()',
        "specifications": '//div[contains(@class, "AdvertCard_specs")]/div/div[contains(@class, "AdvertSpecs_row")]',
        "price": '//div[contains(@class, "AdvertCard_priceBlock")]/div[@data-target="advert-price"]/text()',
    }

    def parse(self, response, **kwargs):
        brands_links = response.xpath(self.xpath_query["brands"])
        yield from self.gen_task(response, brands_links, self.brand_parse)

    def brand_parse(self, response, **kwargs):
        pagination_links = response.xpath(self.xpath_query["pagination"])
        yield from self.gen_task(response, pagination_links, self.brand_parse)
        ads_links = response.xpath(self.xpath_query["ads"])
        yield from self.gen_task(response, ads_links, self.ads_parse)

    def ads_parse(self, response, **kwargs):
        loader = YoulaParseItem(response=response)
        loader.add_value('url', response.url)
        for key, selector in self.itm_template.items():
            loader.add_xpath(key, selector)
        item = loader.load_item()
        yield item

    def gen_task(response, link_list, callback):
        for link in link_list:
            yield response.follow(link, callback=callback)