import json
import requests
import scrapy
from ..loaders import HhVacancyLoader, HhCompanyLoader


class HhruSpider(scrapy.Spider):
    name = "hhru"
    allowed_domains = ["hh.ru"]
    start_urls = ["https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113"]

    xpath_query = {
        'pagination': '//a[@data-qa="pager-page"]/@href',
        'vacancy': '//a[@data-qa="vacancy-serp__vacancy-title"]/@href',
        'company': '//a[@data-qa="vacancy-serp__vacancy-employer"]'
    }

    xpath_vacancy = {
        'title': '//h1//text()',
        'salary': '//p[@class="vacancy-salary"]//text()',
        'description': '//div[@data-qa="vacancy-description"]//text()',
        'skills': '//div[contains(@class, "bloko-tag")]//text()',
        'company_url': '//a[@data-qa="vacancy-company-name"]/@href'
    }

    xpath_company = {
        'prof_area': '//div[@class="employer-sidebar-block"]/p/text()',
        'employer_vacancies': '//a[@data-qa="employer-page__employer-vacancies-link"]/@href',
        'company_site': '//div[@class="employer-sidebar"]//a[@data-qa="sidebar-company-site"]/@href',
        'company_description': '//div[@data-qa="company-description-text"]//text()',
        # for pages with css_class contains "tmpl_hh"
        'company_site_b': '//div[@class="tmpl_hh_wrapper"]//a[@target="_blank"]/@href',
        'prof_area_b': '//span[@data-qa="vacancies-group-title-link"]//text()',
        'employer_vacancies_b': '//div[@class="tmpl_hh_vacancyLink"]/a/@href'
    }

    def company_description_xpath(self, response):
        if response.xpath('//div[contains(@class, "tmpl_hh_banner__content")]//text()') != []:
            return '//div[contains(@class, "tmpl_hh_banner__content")]//text()'
        elif response.xpath('//div[contains(@class, "tmpl_hh_about")]//text()') != []:
            return '//div[contains(@class, "tmpl_hh_about")]//text()'
        else:
            return '//div[contains(@class, "tmpl_hh_future")]//text()'

    def parse(self, response):
        for page in response.xpath(self.xpath_query['pagination']):
            yield response.follow(page, callback=self.parse)

        for vacancy in response.xpath(self.xpath_query['vacancy']):
            yield response.follow(vacancy, callback=self.parse_vacancy)

        for company in response.xpath(self.xpath_query['company']):
            yield response.follow(company.attrib['href'], callback=self.parse_company,
                                  cb_kwargs=dict(name=company.css('::text').get()))

    def parse_vacancy(self, response):
        loader = HhVacancyLoader(response=response)
        loader.add_value('vacancy_url', response.url)
        for key, value in self.xpath_vacancy.items():
            loader.add_xpath(key, value)
        yield loader.load_item()

    def parse_company(self, response, name):
        loader = HhCompanyLoader(response=response)
        loader.add_value('company_url', response.url)
        loader.add_value('company_name', name)
        if response.xpath('//div[@id="HH-React-Error"]') != []:
            loader.add_xpath('company_site', self.xpath_company['company_site'])
            loader.add_xpath('prof_area', self.xpath_company['prof_area'])
            loader.add_xpath('company_description', self.xpath_company['company_description'])
            yield loader.load_item()
        else:
            loader.add_xpath('company_site', self.xpath_company['company_site_b'])
            loader.add_xpath('prof_area', self.xpath_company['prof_area_b'])
            loader.add_xpath('company_description', self.company_description_xpath(response))
            yield loader.load_item()

        if response.xpath(self.xpath_company['employer_vacancies']).get():
            yield response.follow(response.xpath(self.xpath_company['employer_vacancies']).get(), callback=self.parse)
        else:
            yield response.follow(response.xpath(self.xpath_company['employer_vacancies_b']).get(), callback=self.parse)
