import os
import time
import re
import random
import requests
import json
import pandas as pd
import zipfile
from datetime import datetime
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import csv
import gspread
from google.oauth2 import service_account


def get_job_id(job_link):
    """Trích xuất job ID từ LinkedIn job URL"""
    if not job_link or not isinstance(job_link, str):
        return None
    match = re.search(r'view/(\d+)/', job_link)
    if match:
        return match.group(1)  # Lấy số job_id
    return None



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
    return f"LI_{timestamp}_{random_suffix}_{scraping_type}"

# Function to write a start log entry
def write_start_log(log_id, scraping_type, keywords=""):
    sheet.append_row([
            log_id,
            'LinkedIn',
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
            'LinkedIn',
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



####################################
# Login code #######################
####################################

print("Start the Log-in procedure")

### Các bước chuẩn bị
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
# options.add_argument("--disable-infobars")
prefs = {"credentials_enable_service": False,
     "profile.password_manager_enabled": False}
options.add_experimental_option("prefs", prefs)
options.add_argument("--disable-notifications")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
# options.add_argument("user-data-dir=C:\\Users\\trand\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 7")

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

login_error_count = 0
login_errors = []

login_log_id = generate_log_id("SGN")
login_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
write_start_log(login_log_id, "Login", "LinkedIn")

def load_ld_config(config_file):
    config = {}
    with open(config_file, 'r') as file:
        for line in file:
            if "=" in line:              
                key, value = line.strip().split("=", 1)
                config[key.strip()] = value.strip()
    return config

config = load_ld_config(r"C:\working\job_rcm\job_rcm_code\job_scraping\linkedin\linkedin_config.txt")
email_value = config.get("email")
password_value = config.get("password")

try:
    # Launch browser
    driver = webdriver.Chrome(chrome_driver_path, options=options)
    driver.get("https://www.linkedin.com/login")

    # Đăng nhập bằng tài khoản & mật khẩu
    time.sleep(4)
    email = driver.find_element(By.NAME, "session_key")
    password = driver.find_element(By.NAME, "session_password")
    email.send_keys(email_value)
    time.sleep(1)
    password.send_keys(password_value)
    time.sleep(2)

    button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()

    actions = ActionChains(driver)
    time.sleep(3)

    button = driver.find_elements(By.CSS_SELECTOR,"li.global-nav__primary-item")
    job_btn = button[2]
    actions.move_to_element(job_btn).perform()
    time.sleep(1)

    actions.click(job_btn).perform()
except Exception as e:
    error_msg = f"Login failed"
    print('Login failed')
    login_errors.append(error_msg)
    login_error_count += 1


# Log the end of login process
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


base_save_dir = r'C:\working\job_rcm\data\linkedin'
list_info_all = os.path.join(base_save_dir, "list_info_all.csv")

# Lấy thời gian hiện tại
now = datetime.now()
year = now.strftime("%Y")
month = now.strftime("%m")
day = now.strftime("%d")
attempt = now.strftime("Attempt_%H_%M")

# Xây dựng đường dẫn thư mục
year_dir = os.path.join(base_save_dir, year)
month_dir = os.path.join(year_dir, month)
day_dir = os.path.join(month_dir, day)
attempt_dir = os.path.join(day_dir, attempt)
listview_dir = os.path.join(attempt_dir, "Listview")
detailview_dir = os.path.join(attempt_dir, "Detailview")
html_dir = os.path.join(listview_dir, "HTML")

# Tạo thư mục nếu chưa tồn tại
for directory in [year_dir, month_dir, day_dir, attempt_dir, listview_dir, detailview_dir, html_dir]:
    os.makedirs(directory, exist_ok=True)

print(f"Thư mục attempt đã được tạo: {attempt_dir}")


#####################################
# listview code #####################
#####################################

print("Start the listview scrape procedure")

# Log the start of the listview scraping process
listview_log_id = generate_log_id("LSV")
listview_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
write_start_log(listview_log_id, "Listview Scraping")

# Variables to track listview scraping progress
listview_total_jobs = 0
listview_error_count = 0
listview_errors = []

json_file_path = os.path.join(listview_dir, "data.json")
list_info_attempt_path = os.path.join(attempt_dir, "list_info_attempt.csv")
list_info_done_path = os.path.join(attempt_dir, "list_info_done.csv")
detailview_attempt_path = os.path.join(attempt_dir, "detailview_attempt.csv")



# Đảm bảo file JSON tồn tại
json_file_path = os.path.join(listview_dir, "data.json")
if not os.path.exists(json_file_path):
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4, ensure_ascii=False)

# list_info_attempt.csv
if not os.path.exists(list_info_attempt_path):
    with open(list_info_attempt_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["page", "job_index", "job_link", "job_id"])

# Nếu CSV chưa có, tạo file với tiêu đề cột
if not os.path.exists(list_info_done_path):
    with open(list_info_done_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["job_link", "job_id"])

# Nếu CSV chưa có, tạo file với tiêu đề cột
if not os.path.exists(detailview_attempt_path):
    with open(detailview_attempt_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["job_link", "job_id", "job_name", "job_status", "region", "company_name", "company_href", "scrape_date", "hr_id", "jd"])
def get_job_links(page, keyword):
    global listview_error_count, listview_errors
    
    try:
        job_elements = driver.find_elements(By.CSS_SELECTOR, "li.ember-view.occludable-update.scaffold-layout__list-item")
        print(f"Từ khóa '{keyword}' - Trang {page} có {len(job_elements)} công việc.")

        # Đọc dữ liệu JSON hiện có
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Đảm bảo từ khóa có trong JSON
        if keyword not in data:
            data[keyword] = {}

        # Đảm bảo trang hiện tại có trong JSON
        if f"page {page}" not in data[keyword]:
            data[keyword][f"page {page}"] = {
                "path_to_html": os.path.join(html_dir, f"{keyword.replace(' ', '_')}_page{page}_HTML.txt"),
                "jobs": {}
            }

        # Mở tệp CSV để ghi dữ liệu
        with open(list_info_attempt_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Duyệt qua danh sách công việc và lấy link
            for idx, job in enumerate(job_elements, start=1):
                try:
                    actions.move_to_element(job).perform()
                    job_href = job.find_element(By.CSS_SELECTOR, "div.full-width.artdeco-entity-lockup__title.ember-view a").get_attribute("href")
                    data[keyword][f"page {page}"]["jobs"][f"job_{idx}"] = {"link_job": job_href}

                    # Ghi vào CSV
                    writer.writerow([page, idx, job_href])
                except Exception as e:
                    error_msg = f"Lỗi khi lấy link công việc {idx} trên trang {page}"
                    print(error_msg)
                    listview_error_count += 1
                    listview_errors.append(error_msg)

        # Lưu lại dữ liệu vào JSON
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        return len(job_elements)
    
    except Exception as e:
        error_msg = f"Error in get_job_links for page {page}, keyword {keyword}"
        print('Error in get_job_links')
        listview_error_count += 1
        listview_errors.append(error_msg)
        return 0


def page_switch(n, keyword):
    global listview_error_count, listview_errors
    
    total_jobs = 0
    for page in range(1, n + 1):
        try:
            # Lấy nội dung HTML của trang hiện tại
            html_content = driver.page_source
            html_file_path = os.path.join(html_dir, f"{keyword.replace(' ', '_')}_page{page}_HTML.txt")

            # Lưu HTML vào file
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"Đã lưu HTML của trang {page} vào {html_file_path}")

            # Gọi hàm lấy danh sách công việc
            jobs_on_page = get_job_links(page, keyword)
            total_jobs += jobs_on_page

            # Chuyển sang trang tiếp theo nếu không phải trang cuối
            if page < n:
                css_selector = f'li.jobs-search-pagination__indicator button[aria-label="Page {page + 1}"]'
                try:
                    page_button = driver.find_element(By.CSS_SELECTOR, css_selector)
                    actions.move_to_element(page_button).perform()
                    time.sleep(1)
                    actions.click(page_button).perform()
                    print(f"Đang chuyển sang trang {page + 1}")
                    time.sleep(2)  # Chờ trang tải xong
                except Exception as e:
                    error_msg = f"Lỗi khi chuyển trang {page + 1}"
                    print(error_msg)
                    listview_error_count += 1
                    listview_errors.append(error_msg)
                    break  # Thoát nếu không thể chuyển trang
        except Exception as e:
            error_msg = f"Error in page_switch for page {page}, keyword {keyword}"
            print('Error in page_switch')
            listview_error_count += 1
            listview_errors.append(error_msg)
    
    return total_jobs


time.sleep(5)
keyword_list_path = r'C:\working\job_rcm\data\linkedin\job_keywords.csv' # gọi ra các keyword từ file này
df_keywords = pd.read_csv(keyword_list_path, header=None, names=["keyword"])
keywords_list = df_keywords["keyword"].tolist()
all_keywords = ", ".join(keywords_list)



try:
    for word in keywords_list:
        search_box = driver.find_element(By.CSS_SELECTOR,"input.jobs-search-box__text-input.jobs-search-box__keyboard-text-input.jobs-search-global-typeahead__input")
        actions.move_to_element(search_box).perform()
        time.sleep(1)
        search_box.send_keys(word)
        time.sleep(1)
        actions.send_keys(Keys.ENTER).perform()
        time.sleep(5)

        print(f'Đang tìm kiếm công việc với từ khóa: {word}')

        keyword_jobs = page_switch(3, word)
        listview_total_jobs += keyword_jobs

        print(f"Đã hoàn thành tìm kiếm công việc với từ khóa: {word} \n\n\n\n\n\n")
        try:
            search_box = driver.find_element(By.CSS_SELECTOR,"input.jobs-search-box__text-input.jobs-search-box__keyboard-text-input.jobs-search-global-typeahead__input")
            actions.move_to_element(search_box).perform()
            time.sleep(1)
            search_box.clear()
        except Exception as e:
            error_msg = f"Không thể xóa từ khóa tìm kiếm {word}: "
            print('Error in clearing search box')
            listview_error_count += 1
            listview_errors.append(error_msg)

    # Log the end of the listview scraping
    listview_status = 'Success' if listview_error_count == 0 else 'Partial Success'
    
except Exception as e:
    error_msg = f"Error in listview scraping: "
    print('Error in listview scraping')
    listview_error_count += 1
    listview_errors.append(error_msg)
    listview_status = 'Failed'

# Log the end of listview scraping
write_end_log(
    listview_log_id, 
    "Listview Scraping",
    listview_start_time,
    listview_status,
    total_keywords=len(keywords_list),
    total_jobs=listview_total_jobs,
    error_count=listview_error_count,
    error_details="; ".join(listview_errors[-5:]) if listview_errors else "",
    keywords=all_keywords
)

####################################
# Comparing code ###################
####################################
####################################
# Comparing code ###################
####################################

print("Start the comparing procedure")

# Log the start of comparing process
comparing_log_id = generate_log_id("CMP")
comparing_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
write_start_log(comparing_log_id, "Comparing")

# Variables to track comparing progress
comparing_error_count = 0
comparing_errors = []
total_jobs = 0
new_jobs = 0

try:
    list_info_all_path = r'C:\working\job_rcm\data\linkedin\list_info_all.csv'
    
    # Make sure the all info file exists and has the right columns
    if not os.path.exists(list_info_all_path):
        with open(list_info_all_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["job_link", "job_id"])
    
    # Read the attempt file
    list_info_attempt = pd.read_csv(list_info_attempt_path)
    
    # Add job_id column to attempt data if it doesn't exist
    if 'job_id' not in list_info_attempt.columns:
        list_info_attempt['job_id'] = list_info_attempt['job_link'].apply(get_job_id)
    
    # Read the all jobs file
    list_info_all = pd.read_csv(list_info_all_path)
    
    # Add job_id column to all data if it doesn't exist
    if 'job_id' not in list_info_all.columns:
        list_info_all['job_id'] = list_info_all['job_link'].apply(get_job_id)
        # Save updated all data with job_id column
        list_info_all.to_csv(list_info_all_path, index=False)

    # Update total jobs count (before removing duplicates)
    total_jobs_raw = len(list_info_attempt)
    
    # Remove duplicate job_ids within the attempt file itself
    list_info_attempt = list_info_attempt.drop_duplicates(subset=['job_id'], keep='first')
    
    # Count after removing duplicates
    total_jobs = len(list_info_attempt)
    duplicates_in_attempt = total_jobs_raw - total_jobs
    if duplicates_in_attempt > 0:
        print(f"Removed {duplicates_in_attempt} duplicate entries from the attempt file")

    # Create a set of existing job IDs for efficient comparison
    job_ids_all = set(list_info_all['job_id'].dropna())
    
    # Filter out jobs that already exist in list_info_all based on job_id
    list_info_add = list_info_attempt[~list_info_attempt['job_id'].isin(job_ids_all)]
    
    # Update new jobs count
    new_jobs = len(list_info_add)
    list_info_add_path = os.path.join(attempt_dir, "list_info_add.csv")
    
    # Save the result to list_info_add.csv
    list_info_add.to_csv(list_info_add_path, index=False)
    
    # Add these new jobs to the all jobs file
    if new_jobs > 0:
        list_info_all = pd.concat([list_info_all, list_info_add], ignore_index=True)
        list_info_all.to_csv(list_info_all_path, index=False)
        print(f"Added {new_jobs} new jobs to the main database")

    print(f"Found {new_jobs} new jobs out of {total_jobs} total jobs (after removing duplicates)")
    print(f"Saved new job list to {list_info_add_path}")
    comparing_status = 'Success'
    
except Exception as e:
    error_msg = f"Error in comparing process: {str(e)}"
    print(f'Error in comparing process: {str(e)}')
    comparing_error_count += 1
    comparing_errors.append(error_msg)
    comparing_status = 'Failed'

# Log the end of comparing process
write_end_log(
    comparing_log_id, 
    "Comparing", 
    comparing_start_time,
    comparing_status,
    total_jobs=total_jobs,
    new_jobs=new_jobs,
    error_count=comparing_error_count,
    error_details="; ".join(comparing_errors[-5:]) if comparing_errors else ""
)

####################################
# Detail code ######################
####################################

print("Start the detailview scrape procedure")

# Log the start of detail scraping
detail_log_id = generate_log_id("DTL")
detail_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
write_start_log(detail_log_id, "Detail Scraping")

# Variables to track detail scraping progress
detail_error_count = 0
detail_errors = []
successful_details = 0


def detail_scraping(link):
    global detail_error_count, detail_errors  
    
    try:
        print(f"Đang xử lý link: {link}")
        job_id = get_job_id(link)
        
        # Check if job exists BEFORE doing any scraping work
        list_info_all = pd.read_csv(list_info_all_path)
        if 'job_id' not in list_info_all.columns:
            list_info_all['job_id'] = list_info_all['job_link'].apply(get_job_id)
        
        if job_id in list_info_all['job_id'].values:
            print(f"Job ID {job_id} already exists. Skipping...")
            return False  # Skip this job
        
        # job name
        print('job_name')
        try:
            time.sleep(2)
            job_relative_box_element = driver.find_element(By.CSS_SELECTOR, "div.t-14.artdeco-card")
            name = job_relative_box_element.find_element(By.CSS_SELECTOR, 'h1.t-24.t-bold.inline').text
        except Exception as e:
            error_msg = f"Lỗi khi lấy job_name: "
            print(error_msg)
            detail_error_count += 1
            detail_errors.append(error_msg)
            name = None
        
        # job status
        print('job_status')
        try:
            time.sleep(2)
            job_status = job_relative_box_element.find_element(By.CSS_SELECTOR, "span.artdeco-inline-feedback__message").text
        except:
            job_status = "available"

        
        # company name and company href
        print('company_name and company_href')
        try:
            time.sleep(2)
            company_href = job_relative_box_element.find_element(By.CSS_SELECTOR, 'div.job-details-jobs-unified-top-card__company-name a').get_attribute("href")
            company_name = job_relative_box_element.find_element(By.CSS_SELECTOR, "div.job-details-jobs-unified-top-card__company-name a").text
        except Exception as e:
            error_msg = f"Lỗi khi lấy company_name and company_href: "
            print(error_msg)
            detail_error_count += 1
            detail_errors.append(error_msg)
            company_href = None
            company_name = None
        
        # city region
        try:
            time.sleep(2)
            city_region = job_relative_box_element.find_elements(By.CSS_SELECTOR, 'span.tvm__text.tvm__text--low-emphasis')[0].text
        except Exception as e:
            error_msg = f"Lỗi khi lấy city_region: "
            print(error_msg)
            detail_error_count += 1
            detail_errors.append(error_msg)
            city_region = None
        
        # scrape date
        scrape_date = datetime.now().isoformat()

        # hr id
        try:
            time.sleep(2)
            hr_box = driver.find_element(By.CSS_SELECTOR, "div.job-details-people-who-can-help__section")
            hr_id = hr_box.find_element(By.CSS_SELECTOR, "div.display-flex.align-items-center.mt4 a").get_attribute("href")
        except Exception as e:
            error_msg = f"Lỗi khi lấy hr_id: "
            print(error_msg)
            detail_error_count += 1
            detail_errors.append(error_msg)
            hr_id = None
            
        # job description
        try: 
            time.sleep(2)
            jd_see_more = driver.find_element(By.CSS_SELECTOR,'button.jobs-description__footer-button.t-14.t-black--light.t-bold.artdeco-card__action.artdeco-button.artdeco-button--icon-right.artdeco-button--3.artdeco-button--fluid.artdeco-button--tertiary.ember-view')
            ActionChains(driver).move_to_element(jd_see_more).click(jd_see_more).perform()
            time.sleep(2)
            jd = driver.find_element(By.CSS_SELECTOR,"div.jobs-description__content.jobs-description-content.jobs-description__content--condensed").text
        except Exception as e:
            error_msg = f"Lỗi khi lấy jd (job description): "
            print(error_msg)
            detail_error_count += 1
            detail_errors.append(error_msg)
            jd = None

        # job data
        job_data = {
            "job": {
                "job_id" : job_id,
                "company_name": company_name,
                "company_href": company_href,
                "job_name": name,
                "region": city_region,
                "job_status": job_status,
                "scrape_date": scrape_date,
                "hr_id": hr_id,
                "jd": jd
            }
        }
        print(job_data)

        list_info_all = pd.read_csv(list_info_all_path)
        list_info_done = pd.read_csv(list_info_done_path)

        if 'job_id' not in list_info_all.columns:
             list_info_all['job_id'] = list_info_all['job_link'].apply(
                get_job_id(link)
            )
        if 'job_id' not in list_info_done.columns:
            list_info_done['job_id'] = list_info_done['job_link'].apply(
                get_job_id(link)
            )

        # Check if job exists by job_id before adding
        if job_id not in list_info_all['job_id'].values:
            new_data_all = pd.DataFrame({"job_link": [link], "job_id": [job_id]})
            list_info_all = pd.concat([list_info_all, new_data_all], ignore_index=True)
            print(f"Added job_id {job_id} to list_info_all")

        if job_id not in list_info_done['job_id'].values:
            new_data_done = pd.DataFrame({"job_link": [link], "job_id": [job_id]})
            list_info_done = pd.concat([list_info_done, new_data_done], ignore_index=True)
            print(f"Added job_id {job_id} to list_info_done")

        # Save back to CSV
        list_info_all.to_csv(list_info_all_path, index=False)
        list_info_done.to_csv(list_info_done_path, index=False)

        # Update detailview_attempt with job_id
        new_data = {
            "job_link": link,
            "job_id": job_id,  # Add job_id to the CSV data
            "job_name": job_data["job"]["job_name"],
            "job_status": job_data["job"]["job_status"],
            "region": job_data["job"]["region"],
            "company_name": job_data["job"]["company_name"],
            "company_href": job_data["job"]["company_href"],
            "scrape_date": job_data["job"]["scrape_date"],
            "hr_id": job_data["job"]["hr_id"],
            "jd": job_data["job"]["jd"]
        }
        
        detailview_attempt = pd.read_csv(detailview_attempt_path)
        
        # Add job_id column if it doesn't exist in detailview_attempt
        if 'job_id' not in detailview_attempt.columns:
            detailview_attempt_columns = list(detailview_attempt.columns)
            # Add job_id after job_link in the columns list
            job_link_index = detailview_attempt_columns.index('job_link')
            detailview_attempt_columns.insert(job_link_index + 1, 'job_id')
            
            # Create a new dataframe with the updated columns
            new_detailview_attempt = pd.DataFrame(columns=detailview_attempt_columns)
            
            # Copy data from old dataframe to new one
            for col in detailview_attempt.columns:
                new_detailview_attempt[col] = detailview_attempt[col]
            
            # Add job_id column with empty values
            new_detailview_attempt['job_id'] = new_detailview_attempt['job_link'].apply(
                lambda x: re.search(r'view/(\d+)/', x).group(1) if re.search(r'view/(\d+)/', x) else None
            )
            
            detailview_attempt = new_detailview_attempt
        
        # Add new job data
        detailview_attempt = pd.concat([detailview_attempt, pd.DataFrame([new_data])], ignore_index=True)
        detailview_attempt.to_csv(detailview_attempt_path, index=False)

        # Use job_id for folder naming
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        job_folder = os.path.join(detailview_dir, f"{job_id}_{timestamp}")
        os.makedirs(job_folder, exist_ok=True)

        html_file_path = os.path.join(job_folder, "page_source.html")
        with open(html_file_path, "w", encoding="utf-8") as html_file:
            html_file.write(driver.page_source)

        json_file_path = os.path.join(job_folder, "data.json")
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(job_data, json_file, indent=4, ensure_ascii=False)

        print(f"Đã lưu dữ liệu cho job_id {job_id} vào {job_folder}")
        print(json.dumps(job_data, indent=4, ensure_ascii=False))
        
        return True
    except Exception as e:
        error_msg = f"Error in detail_scraping for {link}: "
        print(f'Error in detail_scraping {link}')
        detail_error_count += 1
        detail_errors.append(error_msg)
        return False
    

for link in list_info_add['job_link']:
		# Mở tab mới
		try:	
				driver.execute_script(f"window.open('{link}', '_blank');")
				time.sleep(2)  # Chờ tab mới load (có thể điều chỉnh)
		except:
				print("Không thể mở tab mới!")
				continue

		# Chuyển sang tab mới
		driver.switch_to.window(driver.window_handles[-1])
		print(f"Đang vào: {link}")
		time.sleep(5)  # Chờ trang load (có thể điều chỉnh)
		detail_scraping(link)
		print('đã xử lý xong')

		# Kiểm tra số lượng tab, nếu > 1 thì đóng tab cũ
		if len(driver.window_handles) > 1:
				# time.sleep(10)
				driver.close()  # Đóng tab hiện tại
				driver.switch_to.window(driver.window_handles[0])  # Quay về tab chính
                    
# Đóng trình duyệt khi xong
driver.quit()
# Log the end of detail scraping
# detail_status = 'Success' if detail_error_count == 0 else 'Partial Success'
detail_status = 'Success'
write_end_log(
    detail_log_id, 
    "Detail Scraping", 
    detail_start_time,
    detail_status,
    total_keywords=len(keywords_list),
    total_jobs=len(list_info_add),
    error_count=detail_error_count,
    error_details="; ".join(detail_errors[-5:]) if detail_errors else ""
)