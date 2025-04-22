import os
import time
import re
import random
import requests
from datetime import datetime
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
import json
import csv
from selenium.common.exceptions import NoSuchElementException

post_id_list = set()

def extract_post_id(post_href):
    """Hàm trích xuất post_id từ URL bài viết"""
    match = re.search(r'/posts/(\d+)', post_href)
    return match.group(1) if match else None

def scrape_post(driver, element, actions, post_href_list, group_href):
    """Hàm để lấy thông tin bài viết từ một phần tử web"""
    scrape_time = time.localtime()  # Ghi lại thời gian scrape
    actions.move_to_element(element).perform()
    time.sleep(1)

    # Lấy post href
    try:
        post_href_element = element.find_element(By.CSS_SELECTOR, 
                                    "div.html-div.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1q0g3np a")
        post_href_value = post_href_element.get_attribute('href')
        post_id = extract_post_id(post_href_value)

        # Kiểm tra trùng lặp dựa trên post_id
        if post_id in post_id_list:
            print(f"Bỏ qua bài viết trùng lặp: {post_id}")
            return None
    except NoSuchElementException:
        post_href_value = None
        post_id = None

    # Lấy tên tác giả
    try:
        author_name_element = element.find_elements(By.CSS_SELECTOR, 'span.html-span.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1hl2dhg.x16tdsg8.x1vvkbs')
        author_name_value = author_name_element[0].text.strip()
    except:
        author_name_value = None

    # Chuyển tab và lấy HR ID
    actions.move_to_element(author_name_element[0]).key_down(Keys.CONTROL).click(author_name_element[0]).key_up(Keys.CONTROL).perform()
    time.sleep(2)
    current_tabs = driver.window_handles
    
    if len(current_tabs) > 2:
        driver.switch_to.window(current_tabs[-1])
        try :
                profile_elements = driver.find_elements(By.CSS_SELECTOR, 'a.x1i10hfl.xjbqb8w.x1ejq31n.xd10rxx')
                hr_id_value = profile_elements[6].get_attribute('href')
        except:
                hr_id_value = None
        time.sleep(2)
        driver.close()
        driver.switch_to.window(current_tabs[1])
    else:
        print("Only one tab, no extra tab to close.")

    # Lấy ngày đăng bài
    try:
        hover_elements = element.find_elements(By.CSS_SELECTOR, 'span.html-span.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1hl2dhg.x16tdsg8.x1vvkbs')
        actions.move_to_element(hover_elements[1]).perform()

        time.sleep(5)

        date_element = driver.find_element(By.CSS_SELECTOR, "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1xmvt09.x1nxh6w3.x1sibtaa.xo1l8bm.xzsf02u")
        post_date_value = date_element.text
        print(post_date_value)
    except:
        post_date_value = None

    # Kiểm tra và bấm "Xem thêm" nếu có
    try:
        see_more_button = element.find_element(By.XPATH, ".//div[contains(@class, 'x1i10hfl') and contains(@role, 'button') and contains(text(), 'Xem thêm')]")
        if see_more_button:
            see_more_button.click()
            time.sleep(1)
    except:
        print("No 'see more' button found")

    # Lấy nội dung bài viết
    content_value = None
    try:
        color_content_elements = element.find_elements(By.CSS_SELECTOR, "div.x6s0dn4.x78zum5.xdt5ytf.x5yr21d.xl56j7k.x10l6tqk.x17qophe.x13vifvy.xh8yej3")

        if color_content_elements:
            color_content = color_content_elements[0]
            content_element_1s = color_content.find_elements(By.CSS_SELECTOR, "div.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x1vvkbs")

            content_value = content_element_1s[0].text if content_element_1s else None
        else:
            raise NoSuchElementException
        
    except NoSuchElementException:
        try:
            content_element_2s = element.find_elements(By.CSS_SELECTOR, "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1xmvt09.x1lliihq.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.xudqn12.x3x7a5m.x6prxxf.xvq8zen.xo1l8bm.xzsf02u")
            content_value = content_element_2s[0].text if content_element_2s else None
        except:
            content_value = None

    # Lấy ảnh
    image_elements = element.find_elements(By.TAG_NAME, 'img')
    image_urls = [img.get_attribute('src') for img in image_elements if img.get_attribute('width') and img.get_attribute('height') and int(img.get_attribute('width')) > 300 and int(img.get_attribute('height')) > 300]
    

    # Lưu post_id vào danh sách để tránh trùng lặp
    post_id_list.add(post_id)

    # Lưu dữ liệu bài viết
    post_data = {
					'post_href': post_href_value,
					'author_name': author_name_value,
					'hr_id': hr_id_value,
					'group_id': group_href,
					'scrape_date': time.strftime('%Y-%m-%d %H:%M:%S'),
					'post_date': post_date_value,
					'content': content_value,
					'images': image_urls
		}

    save_post_href_to_csv(post_href_value)  # Vẫn lưu vào CSV nhưng có kiểm tra trùng lặp
    post_href_list.append(post_href_value)

    return post_data