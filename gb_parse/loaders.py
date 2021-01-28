import re
from urllib.parse import urljoin
from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from .items import YoulaParseItem, HhVacancyItem, HhCompanyItem
from .items import InstagramHashtagItem, InstagramHashtagMediaItem


def clear_price(item: str):
    try:
        return float(item.replace("\u2009", ''))
    except ValueError:
        return None

def get_author(item):
    re_str = re.compile(r"youlaId%22%2C%22([0-9|a-zA-Z]+)%22%2C%22avatar")
    result = re.findall(re_str, item)
    return urljoin("https://youla.ru/user/", result[0]) if result else None

def get_description(items):
    return '\n'.join(items)

def get_specifications(data):
    tag = Selector(text=data)
    name = tag.xpath('//div[contains(@class, "AdvertSpecs_label")]/text()').get()
    value = tag.xpath('//div[contains(@class, "AdvertSpecs_data")]//text()').get()
    return {name: value}

def specifications_out(data):
    result = {}
    for itm in data:
        result.update(itm)
    return result

def company_url(text):
    return urljoin('https://hh.ru', text)

class YoulaParseItem(ItemLoader):
    default_item_class = YoulaParseItem
    url_out = TakeFirst()
    title_out = TakeFirst()
    price_in = MapCompose(clear_price)
    price_out = TakeFirst()
    author_in = MapCompose(get_author)
    author_out = TakeFirst()
    description_out = get_description
    specifications_in = MapCompose(get_specifications)
    specifications_out = specifications_out

class HhVacancyLoader(ItemLoader):
    default_item_class = HhVacancyItem
    vacancy_url_out = TakeFirst()
    title_out = TakeFirst()
    salary_out = Join()
    description_out = Join()
    company_url_in = MapCompose(company_url)
    company_url_out = TakeFirst()

class HhCompanyLoader(ItemLoader):
    default_item_class = HhCompanyItem
    company_url_out = TakeFirst()
    company_name_out = TakeFirst()
    company_site_out = TakeFirst()
    company_description_out = Join()

class InstagramHashtagLoader(ItemLoader):
    default_item_class = InstagramHashtagItem
    default_output_processor = TakeFirst()

class InstagramHashtagMediaLoader(ItemLoader):
    default_item_class = InstagramHashtagMediaItem
    default_output_processor = TakeFirst()