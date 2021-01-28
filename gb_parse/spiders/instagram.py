import json
import scrapy
import datetime
from ..loaders import InstagramHashtagLoader, InstagramHashtagMediaLoader


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    start_urls = ['https://www.instagram.com/']
    url_base = 'https://www.instagram.com/graphql/query/?query_hash=9b498c08113f1e09617a1703c22b2f32&variables='

    def __init__(self, login, password, start_hash_tags: list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login = login
        self.password = password
        self.start_hash_tags = [f"/explore/tags/{tag}/" for tag in start_hash_tags]

    def parse(self, response):
        try:
            js_data = self.get_js_data(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.password,
                },
                headers={'X-CSRFToken': js_data['config']['csrf_token']}
            )
        except Exception:
            data = response.json()
            if data['authenticated']:
                for tag in self.start_hash_tags:
                    yield response.follow(tag, callback=self.parse_tag_page)

    def parse_tag_page(self, response):
        data_hashtag = self.get_js_data(response)['entry_data']['TagPage'][0]['graphql']['hashtag']
        for node in data_hashtag['edge_hashtag_to_media']['edges']:
            yield from self.parse_post(response, node)

        while data_hashtag['edge_hashtag_to_media']['page_info']['has_next_page']:
            end_cursor = data_hashtag['edge_hashtag_to_media']['page_info']['end_cursor']
            params = {
                "tag_name": data_hashtag['name'],
                "first": 65,
                "after": end_cursor
            }
            url_query_hash = '{' + ','.join([f'"{key}":"{value}"' if type(value) == str else f'"{key}":{value}' for key,value in params.items()]) + '}'
            yield response.follow(self.url_base + url_query_hash, callback=self.parse_posts)

        loader = InstagramHashtagLoader(response=response)
        loader.add_value('date_parse', datetime.datetime.utcnow())
        loader.add_value('hashtag_id', data_hashtag['id'])
        loader.add_value('hashtag_name', data_hashtag['name'])
        loader.add_value('hashtag_image', data_hashtag['profile_pic_url'])
        yield loader.load_item()

    def parse_posts(self, response):
        data = response.json()['data']['hashtag']['edge_hashtag_to_media']['edges']
        for node in data:
            loader = InstagramHashtagMediaLoader()
            loader.add_value('date_parse', datetime.datetime.utcnow())
            loader.add_value('date_create', node['node']['taken_at_timestamp'])
            loader.add_value('node_id', node['node']['id'])
            loader.add_value('node_owner', node['node']['owner']['id'])
            loader.add_value('display_url', node['node']['display_url'])
            yield loader.load_item()

    def parse_post(self, response, data):
        loader = InstagramHashtagMediaLoader(response=response)
        loader.add_value('date_parse', datetime.datetime.utcnow())
        loader.add_value('date_create', data['node']['taken_at_timestamp'])
        loader.add_value('node_id', data['node']['id'])
        loader.add_value('node_owner', data['node']['owner']['id'])
        loader.add_value('display_url', data['node']['display_url'])
        yield loader.load_item()

    def get_js_data(self, response) -> dict:
        json_text = response.xpath('//script[contains(text(), "window._sharedData")]/text()').get()
        return json.loads(json_text.replace("window._sharedData = ", '')[:-1])