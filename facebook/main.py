import os
import time
import re
import random
import requests
from datetime import datetime
import random
import uuid
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
import gspread
from google.oauth2 import service_account

# Google Sheet setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = r'C:\working\job_rcm\job_rcm_code\job_scraping\job-rcm-luan-0e530aa9b6a0.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open_by_key("1cXvQDtzkcjoYaZ0F2tVqwpLaS14M_00m2Qi8zDAmy_o").worksheet("logs")


####################################
# Log system code ##################
####################################

# Function to generate a unique log ID
def generate_log_id(scraping_type):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_suffix = str(uuid.uuid4())[:3]
    return f"FB_{timestamp}_{random_suffix}_{scraping_type}"

# Function to write a start log entry
def write_start_log(log_id, scraping_type, keywords=""):
    sheet.append_row([
            log_id,
            'Facebook',
            scraping_type,
            'Started',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Start time
            '',  # End time (empty for start log)
            0,   # Duration (0 for start log)
            0,   # Total keywords (will be updated in end log)
            0,   # Total jobs (will be updated in end log)
            0,   # New jobs (will be updated in end log)
            0,   # Error count (will be updated in end log)
            '',  # Error details (will be updated in end log)
            keywords  # Keywords
        ])
    return log_id

# Function to write an end log entry
def write_end_log(log_id, scraping_type, start_time, status, total_keywords=0, total_jobs=0,new_jobs=0, error_count=0, error_details="", keywords=""):
    end_time = datetime.now()
    start_datetime = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    duration = int((end_time - start_datetime).total_seconds())
    
    sheet.append_row([
            log_id,
            'Facebook',
            scraping_type,
            status,
            start_time,
            end_time.strftime('%Y-%m-%d %H:%M:%S'),
            duration,
            total_keywords,
            total_jobs,
            new_jobs,
            error_count,
            error_details,
            keywords
        ])


########################################################
####### Path Setting ###################################
########################################################

# ChromeDriver path
chrome_driver_path = 'C:/Users/trand/chromedriver.exe'

# Setup directory paths
base_save_dir = r'C:\working\job_rcm\data\facebook'
image_save_dir = os.path.join(base_save_dir, 'post_image')
csv_file_path = os.path.join(base_save_dir, 'post_ids.csv')
group_href_csv_path = os.path.join(base_save_dir, 'group_href.csv')




########################################################
####### Options Setting & Functions ####################
########################################################


# Đọc danh sách group từ CSV
def read_group_hrefs():
    groups = []
    if os.path.exists(group_href_csv_path):
        with open(group_href_csv_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Bỏ qua tiêu đề
            for row in reader:
                if len(row) >= 1:
                    groups.append([row[0], row[1] if len(row) > 1 else ""])
    return groups

def update_last_scraped(group_href):
    groups = read_group_hrefs()
    for group in groups:
        if group[0] == group_href:
            group[1] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(group_href_csv_path, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["group_href", "last_scraped"])
        writer.writerows(groups)

group_hrefs = read_group_hrefs()
current_group_index = 0  # Biến lưu trạng thái group hiện tại

def get_next_group_href():
    global current_group_index
    if current_group_index < len(group_hrefs):
        group_href = group_hrefs[current_group_index][0]
        current_group_index += 1
        return group_href
    return None

# Create directory if it does not exist
if not os.path.exists(image_save_dir):
    os.makedirs(image_save_dir)

# Đọc danh sách post_id đã thu thập từ CSV
def read_post_ids_from_csv():
    if not os.path.exists(csv_file_path):
        return set()  # Trả về set rỗng nếu file chưa tồn tại
    post_ids = set()  # Đảm bảo biến post_ids là kiểu set
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # Bỏ qua tiêu đề
        for row in reader:
            if row:  # Kiểm tra nếu row không rỗng
                post_ids.add(row[0])  # Lưu post_id vào set
    return post_ids

# Lưu post_id vào CSV kèm theo scrape_date
def save_post_id_to_csv(group_href,post_id):
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([group_href,post_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

# Hàm chuyển đổi struct_time thành đối tượng datetime
def convert_scrape_time(scrape_time):
    return datetime.fromtimestamp(time.mktime(scrape_time))

# Hàm tạo thư mục theo thời gian scrape
def create_directory_structure(scrape_time):
    scrape_time = convert_scrape_time(scrape_time)  # Chuyển struct_time thành datetime
    year_dir = os.path.join(base_save_dir, scrape_time.strftime("%Y"))
    month_dir = os.path.join(year_dir, scrape_time.strftime("%m"))
    day_dir = os.path.join(month_dir, scrape_time.strftime("%d"))
    hour_dir = os.path.join(day_dir, scrape_time.strftime("%H"))

    for i in range(1, 100):  # Tối đa 100 phần
        part_dir = os.path.join(hour_dir, f'part_{i}')
        if not os.path.exists(part_dir):
            os.makedirs(part_dir)
            return part_dir

        if len(os.listdir(part_dir)) < 300:  # Mỗi thư mục chứa tối đa 300 post
            return part_dir

# Hàm lưu dữ liệu post
def save_post_data(post_data, post_html, images, scrape_time):
    part_dir = create_directory_structure(scrape_time)

    scrape_time_str = convert_scrape_time(scrape_time).strftime('%Y-%m-%d_%H%M%S')  # Thêm giây để đảm bảo tên duy nhất
    detail_folder_name = f"{scrape_time_str}_group_{post_data['group_id'].split('/')[-2]}"
    detail_folder = os.path.join(part_dir, detail_folder_name)
    os.makedirs(detail_folder, exist_ok=True)

    # Lưu file JSON
    json_path = os.path.join(detail_folder, 'data.json')
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(post_data, json_file, ensure_ascii=False, indent=4)

    # Lưu file HTML
    html_path = os.path.join(detail_folder, 'html.txt')
    with open(html_path, 'w', encoding='utf-8') as html_file:
        html_file.write(post_html)

    # Lưu hình ảnh
    image_folder = os.path.join(detail_folder, 'images')
    os.makedirs(image_folder, exist_ok=True)
    for idx, img_url in enumerate(images):
        img_path = os.path.join(image_folder, f'image_{idx+1}.jpg')
        try:
            img_data = requests.get(img_url).content
            with open(img_path, 'wb') as img_file:
                img_file.write(img_data)
        except Exception as e:
            print(f"Error downloading image: {e}")

################# Set up Chrome options and driver #################
def read_config(file_path):
    config = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value
    return config

# Read proxy settings from text file
proxy_config = read_config(r'C:\working\job_rcm\job_rcm_code\config.txt')

PROXY_HOST = proxy_config.get('PROXY_HOST', '')
PROXY_PORT = proxy_config.get('PROXY_PORT', '')
PROXY_USER = proxy_config.get('PROXY_USER', '')
PROXY_PASS = proxy_config.get('PROXY_PASS', '')

# Proxy settings
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

# Path lưu cookie
cookie_file = r"C:\working\job_rcm\job_rcm_code\job_scraping\facebook\facebook_cookies.json"



def extract_post_id(post_href):
    """Hàm trích xuất post_id từ URL bài viết"""
    match = re.search(r'/posts/(\d+)', post_href)
    return match.group(1) if match else None

def scrape_post(driver, element, actions, group_href):
    global post_id_list
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
    

    save_post_id_to_csv(group_href,post_id)
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
    
    # Lưu dữ liệu vào file
    post_html = element.get_attribute('outerHTML')
    save_post_data(post_data, post_html, image_urls, scrape_time)


    return post_data

########################################################
####### Running Selenium ###############################
########################################################

login_error_count = 0
login_errors = []

login_log_id = generate_log_id("SGN")
login_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
write_start_log(login_log_id, "Login", "Facebook")


def load_fb_config(config_file):
    config = {}
    with open(config_file, 'r') as file:
        for line in file:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                config[key.strip()] = value.strip()
    return config

config = load_fb_config("C:\working\job_rcm\job_rcm_code\job_scraping\facebook\fb_config.txt")
email_value = config.get("email")
password_value = config.get("password")



# Launch browser
driver = webdriver.Chrome(chrome_driver_path, options=options)
driver.get("http://www.facebook.com")

# Load cookies nếu có	
try:
    with open(cookie_file, "r") as file:
        cookies = json.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)

    # Refresh để xem có đăng nhập thành công không
    driver.refresh()
    time.sleep(3)

    if "login" not in driver.current_url:
        print("Đăng nhập bằng cookie thành công!")
    else:
        print("Cookie hết hạn, đăng nhập lại...")
        raise Exception("Cookie Expired")
except Exception as e:
    print("Không thể đăng nhập bằng cookie:", str(e))
    
    # Đăng nhập bằng tài khoản & mật khẩu
    time.sleep(4)
    email = driver.find_element(By.NAME, "email")
    password = driver.find_element(By.NAME, "pass")
    email.send_keys(email_value)
    password.send_keys(password_value)

    button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()

    # Chờ trang load hoàn tất
    time.sleep(5)

    # Kiểm tra nếu đăng nhập thành công, lưu cookie mới
    if "login" not in driver.current_url:
        print("Đăng nhập thành công! Lưu cookie mới...")
        
        # Lưu cookie vào file JSON
        cookies = driver.get_cookies()
        with open(cookie_file, "w") as file:
            json.dump(cookies, file, indent=4)
        
        print("Cookies đã được lưu vào", cookie_file)
    else:
        print("Đăng nhập thất bại! Vui lòng kiểm tra lại thông tin tài khoản.")
        error_msg = f"Login failed"
        print('Login failed')
        login_errors.append(error_msg)
        login_error_count += 1

time.sleep(5)

# Ghi log kết thúc đăng nhập
login_status = 'Success' if login_error_count == 0 else 'Failed'
write_end_log(
    login_log_id,
    "Login",
    login_start_time,
    login_status,
    total_keywords=0,
    total_jobs=0,
    new_jobs=0,
    error_count=login_error_count,
    error_details="; ".join(login_errors[-5:]) if login_errors else "",
    keywords=""
)


########################################################
####### Scraping logic #################################
########################################################

login_log_id = generate_log_id("DTL")
login_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
write_start_log(login_log_id, "Detail", "Facebook")

# Duyệt qua các nhóm
group_href = get_next_group_href()
post_id_list = read_post_ids_from_csv()

while group_href:
    print(f"Đang truy cập nhóm: {group_href}")
    post_id_list = read_post_ids_from_csv()
    driver.execute_script(f"window.open('{group_href}');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.execute_script("document.body.style.zoom='60%'")

    post_count = 0  # Reset post count mỗi lần đổi nhóm
    actions = ActionChains(driver)

    # n = input("Nhập số bài đăng cần lấy từ mỗi group (mặc định là 5): ")
    # n = int(n) if n.strip().isdigit() else 5
    n = 5



    while post_count < n:  # Số lượng bài cần thu thập trước khi đổi nhóm
        try:
            feed_element = driver.find_element(By.XPATH, '//*[@role="feed"]')
            post_elements = driver.find_elements(By.XPATH, "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']")
            for element in post_elements:
                
                post_data = scrape_post(driver, element, actions, group_href)
                print(post_data)
                
								
                time.sleep(1)
                post_count += 1
                print(f"Đã thu thập {post_count} bài trong nhóm {group_href}")
                if post_count >= n:
                    break
        except Exception as e:
            print(f"Lỗi khi thu thập bài viết: {e}")
        
        # Cuộn xuống để tải thêm bài
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
    
    print(f"Hoàn thành nhóm {group_href}, cập nhật last_scraped và chuyển sang nhóm tiếp theo...")
    update_last_scraped(group_href)
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
    group_href = get_next_group_href()

print("Không còn nhóm nào để thu thập, dừng chương trình.")
driver.quit()

# Ghi log kết thúc thu thập
write_end_log(
    login_log_id,
    "Detail",
    login_start_time,
    "Success",
    total_keywords=0,
    total_jobs=0,
    new_jobs=0,
    error_count=0,
    error_details="",
    keywords=""
)