import scrapy
from urllib.parse import urljoin
from pymongo import MongoClient


class AutoyoulaSpider(scrapy.Spider):
    name = "autoyoula"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]
    db = MongoClient(
        'mongodb+srv://maximka:78301574@cluster0.9thha.mongodb.net/autoyoula?retryWrites=true&w=majority'
    )['autoyoula']
    collection = db['coll1']

    css_query = {
        "brands": "div.TransportMainFilters_block__3etab a.blackLink",
        "pagination": "div.Paginator_block__2XAPy a.Paginator_button__u1e7D",
        "ads": "article.SerpSnippet_snippet__3O1t2 a.bqlackLink",
    }

    data_query = {
        "title":
        lambda resp: resp.css("div.AdvertCard_advertTitle__1S1Ak::text").get(),
        "price":
        lambda resp: float(
            resp.css('div.AdvertCard_price__3dDCr::text').get().replace(
                "\u2009", '')),
        'images':
        lambda response: [
            i.attrib['src']
            for i in response.css('div.PhotoGallery_photoWrapper__3m7yM img')
        ],
        'params':
        lambda response: [{
            str(i.css('div.AdvertSpecs_label__2JHnS::text').get()):
            i.css('div.AdvertSpecs_data__xK2Qx::text').get()
        } for i in response.css('div.AdvertSpecs_row__ljPcX')],
        'description':
        lambda response: response.css(
            'div.AdvertCard_descriptionInner__KnuRi::text').get(),
        'seller_id':
        '',
    }

    def parse(self, response, **kwargs):
        brands_links = response.css(self.css_query["brands"])
        yield from self.gen_task(response, brands_links, self.brand_parse)

    def brand_parse(self, response):
        pagination_links = response.css(self.css_query["pagination"])
        yield from self.gen_task(response, pagination_links, self.brand_parse)
        ads_links = response.css(self.css_query["ads"])
        yield from self.gen_task(response, ads_links, self.ads_parse)

    def ads_parse(self, response):
        data = {}
        for key, selector in self.data_query.items():
            try:
                for script_text in response.css('script').getall():
                    if script_text.find('avatar') > 0:
                        seller_id = 'user/' + script_text[
                            script_text.rfind('youlaId%22%2C%22') +
                            16:script_text.find('%22%2C%22avatar')]
                        seller_id = urljoin('https://youla.ru/', seller_id)
                        break
                    if script_text.find('sellerLink') > 0:
                        seller_id = script_text[
                            script_text.rfind('sellerLink%22%2C%22') +
                            19:script_text.find('%22%2C%22type')].replace(
                                '%2F', '/')
                        seller_id = urljoin('https://auto.youla.ru/',
                                            seller_id)
                data[key] = selector(response)
                data['params'][0]['Год выпуска'] = response.css(
                    'div.AdvertSpecs_row__ljPcX a::text').get()
                data['seller_id'] = seller_id
                self.collection.insert_one(data)
                print(2)
            except (ValueError, AttributeError):
                print(1)
                continue

    def gen_task(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib["href"], callback=callback)