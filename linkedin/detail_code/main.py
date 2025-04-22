import os
import time
import json
import re
import random
import requests
import random
import pandas as pd
import zipfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup


### Các bước chuẩn bị
# Function to read proxy config from file
def read_proxy_config(file_path):
    config = {}
    with open(file_path, 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            config[key] = value
    return config

# Read proxy settings from text file
proxy_config = read_proxy_config(r'C:\working\job_rcm\job_rcm_code\config.txt')
PROXY_HOST = proxy_config['PROXY_HOST']
PROXY_PORT = proxy_config['PROXY_PORT']
PROXY_USER = proxy_config['PROXY_USER']
PROXY_PASS = proxy_config['PROXY_PASS']

# ChromeDriver path
chrome_driver_path = 'C:/Users/trand/chromedriver.exe'

# Manifest for proxy
manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""

# Background script for proxy
background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

# Set up Chrome options
options = Options()
options.add_argument("--disable-infobars")
prefs = {"credentials_enable_service": False,
     "profile.password_manager_enabled": False}
options.add_experimental_option("prefs", prefs)
options.add_argument("--disable-notifications")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# Randomize User-Agent
user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
]
options.add_argument(f"user-agent={random.choice(user_agents)}")
	
# Set up proxy
pluginfile = 'proxy_auth_plugin.zip'
with zipfile.ZipFile(pluginfile, 'w') as zp:
    zp.writestr("manifest.json", manifest_json)
    zp.writestr("background.js", background_js)
options.add_extension(pluginfile)

# Launch browser
driver = webdriver.Chrome(chrome_driver_path, options=options)
driver.get("https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin")
# Login 
time.sleep(4)
email = driver.find_element(By.NAME, "session_key")
password = driver.find_element(By.NAME, "session_password")
email.send_keys("luantran121204@gmail.com")
time.sleep(1)

password.send_keys("tranduyluan11062003")
time.sleep(2)

button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()



################################################
################################################ CÀO DETAIL VÀ LƯU DỮ LIỆU
################################################

time.sleep(5)

import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import os
import time

# Tập hợp các từ khóa ngành nghề
key_words = {'finance','data', 'dev','hr', 'marketing', 'sale'}

# Duyệt qua từng từ khóa ngành nghề
for key in key_words: 
    # Đường dẫn tới tệp danh sách công việc theo ngành
    listview_path = f'C:\\working\\job_rcm\\data\\linkedin\\{key}\\listview\\data.json'
    print(listview_path)

    # Tải dữ liệu ban đầu từ tệp data.json trong listview
    with open(listview_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Danh sách các liên kết công việc
    links = [job_data["link_job"] for page_data in data.values() for job_data in page_data.get("jobs", {}).values()]

    # Tạo thư mục chi tiết nếu chưa tồn tại
    detail_view_folder = f'C:\\working\\job_rcm\\data\\linkedin\\detailview\\{key}'
    os.makedirs(detail_view_folder, exist_ok=True)
    
    detail_view_file_path = os.path.join(detail_view_folder, 'data.json')

    # Danh sách để lưu dữ liệu các công việc đã cào
    jobs_data = []

    # Duyệt qua từng link job
    for link in links:
                try:
                        print(f"Đang xử lý link: {link}")
                        driver.execute_script(f"window.open('{link}', '_blank');")
                        tabs = driver.window_handles
                        time.sleep(3)
                        driver.switch_to.window(tabs[-1])
                        time.sleep(1)

                        # Lấy thông tin công việc
                        job_relative_box_element = driver.find_element(By.CSS_SELECTOR, "div.t-14.artdeco-card")
                        name = job_relative_box_element.find_element(By.CSS_SELECTOR, 'h1.t-24.t-bold.inline').text

                        # Lấy trạng thái công việc (nếu có)
                        try:
                                job_status = job_relative_box_element.find_element(By.CSS_SELECTOR, "span.artdeco-inline-feedback__message").text
                        except:
                                job_status = "available"

                        # Lấy tên và link công ty
                        company_href = job_relative_box_element.find_element(By.CSS_SELECTOR, 'div.job-details-jobs-unified-top-card__company-name a').get_attribute("href")
                        company_name = job_relative_box_element.find_element(By.CSS_SELECTOR, "div.job-details-jobs-unified-top-card__company-name a").text

                        # Thông tin khu vực
                        city_region = job_relative_box_element.find_elements(By.CSS_SELECTOR, 'span.tvm__text.tvm__text--low-emphasis')[0].text

                        # Ngày lấy thông tin
                        scrape_date = datetime.now().isoformat()

                        # ID của HR nếu có
                        try:
                                hr_box = driver.find_element(By.CSS_SELECTOR, "div.job-details-people-who-can-help__section")
                                hr_id = hr_box.find_element(By.CSS_SELECTOR, "div.display-flex.align-items-center.mt4 a").get_attribute("href")
                        except:
                                hr_id = None

                        # Lấy mô tả công việc
                        time.sleep(1)
                        jd_see_more = driver.find_element(By.CSS_SELECTOR, 'button.jobs-description__footer-button.t-14.t-black--light.t-bold.artdeco-card__action.artdeco-button.artdeco-button--icon-right.artdeco-button--3.artdeco-button--fluid.artdeco-button--tertiary.ember-view')
                        ActionChains(driver).move_to_element(jd_see_more).click(jd_see_more).perform()
                        time.sleep(1)
                        jd = driver.find_element(By.CSS_SELECTOR, "div.jobs-description__content.jobs-description-content.jobs-description__content--condensed").text

                        # Tạo JSON cho công việc
                        job_data = {
                                "job_link" : link,
                                "company_name": company_name,
                                "company_href": company_href,
                                "job_name": name,
                                "region": city_region,
                                "job_status": job_status,
                                "scrape_date": scrape_date,
                                "hr_id": hr_id,
                                "jd": jd
                        }
                        jobs_data.append(job_data)
                        
                        # Lưu vào tệp JSON sau mỗi vòng lặp
                        with open(detail_view_file_path, 'w', encoding='utf-8') as file:
                                json.dump({"jobs": jobs_data}, file, ensure_ascii=False, indent=4)
                                print('lưu dữ liệu thành công')

                        # Đóng tab
                        while len(driver.window_handles) > 1:
                                driver.switch_to.window(driver.window_handles[-1])
                                driver.close()
                                time.sleep(1)
                        tabs = driver.window_handles
                        driver.switch_to.window(tabs[0])

                except Exception as e:
                        print(f"Link không hoạt động: {link}")
    links = [] # reset lại list