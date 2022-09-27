import json
import scrapy
import re
from ..loaders import InstagramUsersItemLoader


class InstagramUsersSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    start_urls = ['https://www.instagram.com/']
    api_url = 'https://www.instagram.com/graphql/query/'
    query_hash = {
        'edge_followed_by': 'c76146de99bb02f6415203be841dd25a',
        'edge_follow': 'd04b0a864b4b54837c0d870b0e77e076'
    }
    variables = {
        "id": '',
        "include_reel": True,
        "fetch_mutual": True,
        "first": 24
    }

    def __init__(self, login, password, list_users: list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login = login
        self.password = password
        self.start_list_users = [f"/{user}/" for user in list_users]

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
                for user in self.start_list_users:
                    yield response.follow(user, callback=self.parse_user_page)

    def parse_user_page(self, response):
        data = self.get_js_data(response)['entry_data']
        for key in self.query_hash:
            if data['ProfilePage'][0]['graphql']['user'][key]['count']:
                self.variables["id"] = data['ProfilePage'][0]['graphql']['user']['id']
                url = f'{self.api_url}?query_hash={self.query_hash[key]}&variables={json.dumps(self.variables)}'
                yield response.follow(url, callback=self.parse_follow_, cb_kwargs=dict(key=key))

    def parse_follow_(self, response, key):
        edge_follow_ = response.json()['data']['user'][key]
        if edge_follow_['page_info']['has_next_page']:
            end_cursor = edge_follow_['page_info']['end_cursor']
            self.variables["after"] = end_cursor
            url = f'{self.api_url}?query_hash={self.query_hash[key]}&variables={json.dumps(self.variables)}'
            self.variables["after"] = ''
            yield response.follow(url, callback=self.parse_follow_, cb_kwargs=dict(key=key))

        yield from self.parse_users_follow_(response, edge_follow_['edges'], key)

    def parse_users_follow_(self, response, edges, key):
        for node in edges:
            loader = InstagramUsersItemLoader(response=response)
            for i in self.query_hash:
                if i == key:
                    loader.add_value(i, [node['node']['username'], node['node']['id']])
                else:
                    loader.add_value(i, self.decoder_url(response.url))
            yield loader.load_item()

    def get_js_data(self, response) -> dict:
        json_text = response.xpath('//script[contains(text(), "window._sharedData")]/text()').get()
        return json.loads(json_text.replace("window._sharedData = ", '')[:-1])

    @staticmethod
    def decoder_url(text):
        re_str = re.compile(r'id%22:%20%22([0-9|a-zA-Z]+)%22')
        result = re.findall(re_str, text)
        return result