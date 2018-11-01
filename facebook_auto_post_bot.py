import os
from datetime import datetime
from time import sleep
from urllib import parse
import time
import re
import lxml.html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FFOptions
from googletrans import Translator
from constants import *
# from myLogger import logger, get_main_dir
import logging
logging.basicConfig(format='%(levelname)s: %(message)s')
logger = logging.getLogger()


class FacebookBot:
    def __init__(self):
        logger.info('Preparing Browser...')
        self.base_url = 'https://www.facebook.com/'
        self.translator = Translator(service_urls=[
            'translate.google.com',
            'translate.google.co.kr',
        ])
        self.driver = webdriver.PhantomJS()
        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(60)

    def login(self, username, password):
        logger.info('LogIn...')
        logger.info('\tOpening Login Page...')
        self.driver.get(self.base_url)
        sleep(2)

        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.NAME, 'email')))
        logger.info('\tLogging In As {}...'.format(username))
        self.driver.find_element_by_name('email').clear()
        self.driver.find_element_by_name('email').send_keys(username)
        sleep(1)
        self.driver.find_element_by_name('pass').clear()
        self.driver.find_element_by_name('pass').send_keys(password)
        sleep(1)
        self.driver.find_element_by_name('pass').submit()
        sleep(2)

        if len(self.driver.find_elements_by_xpath('//div[@data-click="profile_icon"]')) > 0:
            logger.info('Login Successful!')
            return True
        else:
            logger.info('Login FAILED!')
            return False

    def scrape_posts_single_page(self, page_url):
        logger.info('\tOpening Page...')
        self.driver.get(page_url)
        sleep(2)
        posts = self.get_new_posts()
        for post in posts:
            post['message'] = self.translate_post(post['message'])

    def create_new_post(self):
        self.driver.get(self.base_url)
        time.sleep(3)
        first_what_is_on_my_mind_element = self.driver.find_element_by_class_name("_5qtp")
        first_what_is_on_my_mind_element.click()
        time.sleep(3)
        msg = 'test'
        # post text
        second_what_is_on_my_mind_element = self.driver.switch_to.active_element
        second_what_is_on_my_mind_element.send_keys(msg)
        time.sleep(1)

        # post image/video
        # os.getcwd() + "/test.jpg"
        file = '/Users/mykhailomykytyn/Projects/upwork_projects/facebook_automated_bot/test.jpeg'
        file_input = self.driver.find_element_by_xpath('//div[@class="_3jk"]/input[contains(@accept, "video/*,")]')
        # print(file_input)
        file_input.send_keys(file)
        time.sleep(5)
        button = self.driver.find_element_by_xpath('//button[@data-testid="react-composer-post-button"]')
        button.click()
        time.sleep(5)

    def translate_post(self, original_post_text):
        transtlated_text = self.translator.translate(original_post_text, dest='fr').text
        return transtlated_text

    def get_new_posts(self):
        logger.info('\tProcessing Page...')
        doc = lxml.html.fromstring(self.driver.page_source)
        doc.make_links_absolute(self.driver.current_url)
        post_dict = dict()
        posts = []
        for article_div in doc.xpath('//div[@id="pagelet_timeline_main_column"]/div/div/div[@class="_1xnd"]/child::*'):
            article_time = article_div.xpath('div/div/div/div/div/div/div/div/div/div/div/div/div/div/span/span/a/abbr/@data-utime')
            if article_time:
                article_time = int(article_time[0])
                delta = datetime.now() - datetime.utcfromtimestamp(article_time)
                if delta.seconds / 60 > 60:
                    continue
            message = ' '.join(article_div.xpath('div/div/div/div/div/div/div[@data-ad-preview="message"]/p/text()')).strip(' ')
            message = re.sub(' +', ' ', message)
            logger.info('message %s' % message)
            post_dict['message'] = message
            attached_photos = article_div.xpath('div/div/div/div/div/div/div/div/div[@class="mtm"]/div/a/@href')
            attached_links = article_div.xpath('div/div/div/div/div/div/div/div/div[@class="mtm"]/div/div/div/span/div/a/@href')
            attached_videos = []
            post_dict['photos'] = attached_photos
            post_dict['links'] = attached_links
            post_dict['videos'] = attached_videos
            print('\n\n')
            posts.append(post_dict)
        return posts


if __name__ == '__main__':
    browser = FacebookBot()
    # browser.login(LOGIN, PASSWORD)
    browser.scrape_posts_single_page('https://www.facebook.com/pg/Oilers.NHL/posts/')
    #browser.create_new_post()
    #browser.driver.get_screenshot_as_file('temp.png')
    browser.driver.quit()
