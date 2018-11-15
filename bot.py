import re
import logging
import random
import string
import json
from time import sleep
from datetime import datetime
import urllib.request
import lxml.html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from apscheduler.schedulers.blocking import BlockingScheduler
from googletrans import Translator

from constants import *

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def find_values(id, json_repr):
    results = []

    def _decode_dict(a_dict):
        try: results.append(a_dict[id])
        except KeyError: pass
        return a_dict

    json.loads(json_repr, object_hook=_decode_dict)
    return results


class FacebookBot:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        logger.info('Preparing Browser...')
        self.base_url = 'https://www.facebook.com/'
        self.translator = Translator(service_urls=[
            'translate.google.com',
            'translate.google.co.kr',
        ])
        self.driver = webdriver.PhantomJS()
        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(60)

    def login(self):
        logger.info('LogIn...')
        logger.info('\tOpening Login Page...')
        self.driver.get(self.base_url)
        sleep(2)

        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.NAME, 'email')))
        logger.info('\tLogging In As {}...'.format(self.username))
        self.driver.find_element_by_name('email').clear()
        self.driver.find_element_by_id('email').send_keys(self.username)
        sleep(1)
        self.driver.find_element_by_name('pass').clear()
        self.driver.find_element_by_name('pass').send_keys(self.password)
        sleep(1)
        self.driver.find_element_by_name('pass').submit()
        sleep(2)

        if len(self.driver.find_elements_by_xpath('//div[@data-click="profile_icon"]')) > 0:
            logger.info('Login Successful!')
            return True
        else:
            logger.info('Login FAILED!')
            return False

    def run(self, pages_list):
        self.login()
        for page_url in pages_list:
            logger.info('\tOpening Page...')
            posts = self.get_new_posts(page_url.replace('www', 'mbasic'))
            translated_posts = self.translate_post(posts)

            for post in translated_posts:
                self.create_new_posts(post)

    @staticmethod
    def send_file_to_form(url, filename):
        urllib.request.urlretrieve(url, filename)
        return '/Users/mykhailomykytyn/Projects/upwork_projects/facebook_automated_bot/{}'.format(filename)

    def create_new_posts(self, post):
        self.driver.get(self.base_url)
        sleep(3)
        first_what_is_on_my_mind_element = self.driver.find_element_by_class_name("_5qtp")
        first_what_is_on_my_mind_element.click()
        sleep(3)
        # post text
        second_what_is_on_my_mind_element = self.driver.switch_to.active_element
        second_what_is_on_my_mind_element.send_keys(post['message'])
        second_what_is_on_my_mind_element.send_keys('\n')
        for link in post['links']:
            second_what_is_on_my_mind_element.send_keys(link)
            sleep(1)
        for photo_url in post['photos']:
            second_what_is_on_my_mind_element.send_keys('\n')
            file_input = self.driver.find_element_by_xpath('//div[@class="_3jk"]/input[contains(@accept, "video/*,")]')
            file_input.send_keys(self.send_file_to_form(photo_url, 'tmp.png'))
        for video_url in post['videos']:
            file_input = self.driver.find_element_by_xpath('//div[@class="_3jk"]/input[contains(@accept, "video/*,")]')
            file_input.send_keys(self.send_file_to_form(video_url, 'tmp.mp4'))
        sleep(20)
        button = self.driver.find_element_by_xpath('//button[@data-testid="react-composer-post-button"]')
        button.click()
        sleep(5)

    def translate_post(self, posts):
        for post in posts:
            translated_text = self.translator.translate(post['message'], dest='fr').text
            post['message'] = translated_text
        return posts

    @staticmethod
    def parse_article(article_div):
        post_dict = dict()
        message = ' '.join(article_div.xpath('div[@class="gq"]/div[@class="gy"]/span/descendant::*/text()')).strip(' ')
        message = re.sub(' +', ' ', message)
        logger.info('message %s' % message)
        post_dict['message'] = message
        attached_photos = article_div.xpath('div/div/div/div[class="hi hj"]/a/@href')
        attached_links = article_div.xpath('div[@class="gq"]/div/a/@href')
        attached_videos = article_div.xpath('div/div/div/div[@class="hj"]/a/@href')
        print('attached video', attached_videos)
        print('attached photos', attached_photos)
        print('attached links', attached_links)
        sleep(12)
        post_dict['photos'] = attached_photos
        post_dict['links'] = attached_links
        post_dict['videos'] = attached_videos
        return post_dict

    def get_new_posts(self, page_url):
        self.driver.get(page_url)
        sleep(2)
        logger.info('Processing Page...')
        doc = lxml.html.fromstring(self.driver.page_source)
        doc.make_links_absolute(self.driver.current_url)
        posts = []
        while True:
            for article_div in doc.xpath('//div[@class="gl gm gn"]/child::*'):
                data_fi = json.dumps(json.loads(article_div.xpath('@data-ft')[0]))
                article_time = find_values('publish_time', data_fi)[0]
                print('article time', datetime.utcfromtimestamp(article_time))
                if article_time:
                    article_time = int(article_time[0])
                    delta = datetime.now() - datetime.utcfromtimestamp(article_time)
                    if delta.seconds / 60 > 60:
                        return posts
                post_dict = self.parse_article(article_div)
                posts.append(post_dict)
            next_posts = self.driver.find_element_by_xpath('//div[@id="timelineBody"]/div[@class="i"]/a')
            next_posts.click()
            sleep(10)


def run_bot():
    logging.info('START')
    browser = FacebookBot(LOGIN, PASSWORD)
    browser.run(TEAM_PAGES)
    browser.driver.quit()


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(run_bot(), 'interval', hours=1)
    scheduler.start()
