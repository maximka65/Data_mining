import json

import scrapy
import datetime
from ..loaders import InstagramHashtagLoader, InstagramHashtagMediaLoader, InstagramUsersItemLoader
from scrapy.exceptions import CloseSpider


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    start_urls = ['https://www.instagram.com/']
    api_url = 'https://www.instagram.com/graphql/query/'
    query_hash_t = {
        'tag_posts': "9b498c08113f1e09617a1703c22b2f32"
    }
    query_hash_u = {
        'edge_followed_by': 'c76146de99bb02f6415203be841dd25a',
        'edge_follow': 'd04b0a864b4b54837c0d870b0e77e076'
    }

    def __init__(self, login, password, start_hash_tags=None, list_users=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login = login
        self.password = password
        if start_hash_tags:
            self.start_hash_tags = [f"/explore/tags/{tag}/" for tag in start_hash_tags]
        if list_users:
            self.start_point = list_users[0]
            self.end_point = list_users[1]

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
                #for tag in self.start_hash_tags:
                    #yield response.follow(tag, callback=self.parse_tag_page)
                yield response.follow(f'/{self.start_point}/', callback=self.parse_user_page)

    def parse_user_page(self, response, parent=None):
        data = self.get_js_data(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        variables = {
            "id": data['id'],
            "first": 50
        }
        user = {
            'user_id': data['id'],
            'username': data['username'],
            'count': data['edge_followed_by']['count'] + data['edge_follow']['count'],
            'links': []
            }
        if parent:
            user['parent'] = parent
        else:
            user['parent'] = ''

        for key in self.query_hash_u:
            url = f'{self.api_url}?query_hash={self.query_hash_u[key]}&variables={json.dumps(variables)}'
            yield response.follow(url, callback=self.parse_follow_, cb_kwargs=dict(key=key, user=user))

    def parse_follow_(self, response, key, user):
        if b'application/json' in response.headers['Content-Type']:
            edge_follow_ = response.json()['data']['user'][key]
            yield from self.parse_users_follow_(edge_follow_['edges'], user)

            if edge_follow_['page_info']['has_next_page']:
                variables = {
                    "id": user['user_id'],
                    "first": 50,
                    "after": edge_follow_['page_info']['end_cursor']
                }
                url = f'{self.api_url}?query_hash={self.query_hash_u[key]}&variables={json.dumps(variables)}'
                yield response.follow(url, callback=self.parse_follow_, cb_kwargs=dict(key=key, user=user))

            if len(user['links']) == user['count']:
                if user['parent'] == '':
                    parent = user['username']
                else:
                    parent = user['parent'] + ' => ' + user['username']
                user['links'] = self.get_handshake(user)
                with open('links.txt', 'a') as f:
                    for link in user['links']:
                        f.write(' '.join(link) + ' ' + user['parent'] + '\n')

                yield from self.gen_new_start_points(response, parent)

    def gen_new_start_points(self, response, parent):
        links = []
        with open('links.txt') as f:
            for line in f:
                links.append(line)
        next_start_user = links.pop(0).split()[1]
        with open('links.txt', 'w') as f:
            for link in links:
                f.write(link)
            yield response.follow(f'/{next_start_user}/', callback=self.parse_user_page, cb_kwargs=dict(parent=parent))

    @staticmethod
    def parse_users_follow_(edges, user):
        for node in edges:
            user['links'].append([node['node']['id'], node['node']['username']])
        yield user

    def get_handshake(self, user):
        handshake = []
        while len(user['links']):
            is_hand = user['links'].pop()
            if user['links'].count(is_hand):
                handshake.append(is_hand)
                user['links'].remove(is_hand)
                if is_hand[1] == self.end_point:
                    self.print_handshake(user)
                    raise CloseSpider('success')
        return handshake

    def print_handshake(self, user):
        if user['parent'] == '':
            print(f'{self.start_point} => {self.end_point}')
            with open('rezult.json', 'w') as f:
                json.dump(user, f)
        else:
            print(f'{user["parent"]} => {user["username"]} => {self.end_point}')
            with open('rezult.json', 'w') as f:
                json.dump(user['parent'], f)

    def close(spider, reason):
        if reason == 'finished':
            print('Between users no handshake')

    def parse_tag_page(self, response):
        data_hashtag = self.get_js_data(response)['entry_data']['TagPage'][0]['graphql']['hashtag']
        for node in data_hashtag['edge_hashtag_to_media']['edges']:
            yield from self.parse_post(response, node)

        while data_hashtag['edge_hashtag_to_media']['page_info']['has_next_page']:
            params = {
                "tag_name": data_hashtag['name'],
                "first": 65,
                "after": data_hashtag['edge_hashtag_to_media']['page_info']['end_cursor']
            }
            url = f'{self.api_url}?query_hash={self.query_hash_t["tag_posts"]}&variables={json.dumps(params)}'
            yield response.follow(url, callback=self.parse_posts)

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

    @staticmethod
    def get_js_data(response) -> dict:
        json_text = response.xpath('//script[contains(text(), "window._sharedData")]/text()').get()
        return json.loads(json_text.replace("window._sharedData = ", '')[:-1])