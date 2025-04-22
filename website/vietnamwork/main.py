import os
import time
import re
import random
import requests
import random
import json
import pandas as pd
import zipfile
import uuid
from datetime import datetime
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
    return f"VI_{timestamp}_{random_suffix}_{scraping_type}"

# Function to write a start log entry
def write_start_log(log_id, scraping_type, keywords=""):
    sheet.append_row([
            log_id,
            'VietnamWorks',
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
            'VietnamWorks',
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

login_error_count = 0
login_errors = []

login_log_id = generate_log_id("SGN")
login_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
write_start_log(login_log_id, "Login")

### Các bước chuẩn bị
def read_config(file_path):
    config = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value
    return config


# ChromeDriver path
chrome_driver_path = 'C:/Users/trand/chromedriver.exe'



# Set up Chrome options
options = Options()
# options.add_argument("--disable-infobars")
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

# Launch browser
driver = webdriver.Chrome(chrome_driver_path, options=options)
driver.get("https://www.vietnamworks.com")
actions = ActionChains(driver)
time.sleep(3)
search_btn = driver.find_element(By.CSS_SELECTOR,"button.sc-cspYLC.hYKSlj.btn-primary.btn-md.search__button.clickable")
actions.move_to_element(search_btn).click(search_btn).perform()

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




base_save_dir = r'C:\working\job_rcm\data\vietnamwork'
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

# Nếu CSV chưa có, tạo file với tiêu đề cột
if not os.path.exists(list_info_attempt_path):
    with open(list_info_attempt_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["page", "job_index", "job_link"])  # Tiêu đề cột

# Nếu CSV chưa có, tạo file với tiêu đề cột
if not os.path.exists(list_info_done_path):
    with open(list_info_done_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["job_link"])  # Tiêu đề cột

# Nếu CSV chưa có, tạo file với tiêu đề cột
if not os.path.exists(detailview_attempt_path):
    with open(detailview_attempt_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["job_link", "job_name", "job_status", "region", "company_name", "company_href", "scrape_date", "hr_id", "jd"])  # Tiêu đề cột

def get_job_links(page, keyword):
    global listview_error_count, listview_errors

    try :
            job_board = driver.find_element(By.CSS_SELECTOR, "div.block-job-list")
            current_job_elements = job_board.find_elements(By.CSS_SELECTOR, "div.sc-iVDsrp.frxvCT")
            job_elements = set(current_job_elements)  # Sử dụng set để tránh trùng lặp công việc

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

                while True:
                    # Di chuyển đến các phần tử công việc mới
                    for job in current_job_elements:
                        actions.move_to_element(job).perform()

                    # Cập nhật danh sách các công việc sau khi đã di chuyển đến các phần tử mới
                    current_job_elements = job_board.find_elements(By.CSS_SELECTOR, "div.sc-iVDsrp.frxvCT")
                    new_jobs = set(current_job_elements) - job_elements  # Lấy các công việc mới
                    job_elements.update(new_jobs)  # Cập nhật job_elements với các công việc mới

                    # Dừng lại nếu không còn công việc mới
                    if not new_jobs:
                        break

                # Thông báo số lượng công việc khi đã thu thập xong
                print(f"Từ khóa '{keyword}' - Trang {page} có {len(job_elements)} công việc.")

                # Duyệt qua danh sách công việc và lấy link
                for idx, job in enumerate(job_elements, start=1):
                    try:
                        job_href = job.find_element(By.CSS_SELECTOR, "a.img_job_card").get_attribute("href")
                        data[keyword][f"page {page}"]["jobs"][f"job_{idx}"] = {"link_job": job_href}

                        # Ghi vào CSV
                        writer.writerow([page, idx, job_href])
                    except Exception as e:
                        print(f"Lỗi khi lấy link công việc {idx} trên trang {page}")

            # Lưu lại dữ liệu vào JSON
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
    except:
            error_msg = f"Error in get_job_links for page {page}, keyword {keyword}"
            print('Error in get_job_links')
            listview_error_count += 1
            listview_errors.append(error_msg)
            return 0

    
def page_switch(n,keyword):
    global listview_error_count, listview_errors

    total_jobs = 0

    for page in range(1, n + 1):
        try:
             # Lấy nội dung HTML của trang hiện tại
            html_content = driver.page_source
            keyword_dir = os.path.join(html_dir,f"{keyword.replace(' ', '_')}")
            os.makedirs(keyword_dir, exist_ok=True)
            html_file_path = os.path.join(keyword_dir, f"page{page}_HTML.txt")

            # Lưu HTML vào file
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"Đã lưu HTML của trang {page} vào {html_file_path}")

            # Gọi hàm lấy danh sách công việc
            jobs_on_page = get_job_links(page, keyword)
            total_jobs += jobs_on_page

            # Chuyển sang trang tiếp theo nếu không phải trang cuối
            if page < n:
                xpath_selector  = f"//li[@class='page-item btn-default']/button[text()='{page + 1}']"
                try:
                    page_button = driver.find_element(By.XPATH, xpath_selector)
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
        except:
            error_msg = f"Error in page_switch for page {page}, keyword {keyword}"
            print('Error in page_switch')
            listview_error_count += 1
            listview_errors.append(error_msg)
            break
    return total_jobs


time.sleep(5)
keyword_list_path = r'C:\working\job_rcm\data\vietnamwork\job_keywords.csv' # gọi ra các keyword từ file này
df_keywords = pd.read_csv(keyword_list_path, header=None, names=["keyword"])
keywords_list = df_keywords["keyword"].tolist()
all_keywords = ", ".join(keywords_list)

try :
    for word in df_keywords["keyword"]:
        # Format the URL with the keyword
        url = f"https://www.vietnamworks.com/viec-lam?q={word}"
        
        # Navigate directly to the search results page
        driver.get(url)
        time.sleep(5)
        
        print(f'Đang tìm kiếm công việc với từ khóa: {word}')
        page_switch(1, word)
        print(f"Đã hoàn thành tìm kiếm công việc với từ khóa: {word} \n\n\n\n")
    listview_status = 'Success'
except :
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

try :
    list_info_all_path = r'C:\working\job_rcm\data\vietnamwork\list_info_all.csv'
    list_info_attempt = pd.read_csv(list_info_attempt_path)
    list_info_all = pd.read_csv(list_info_all_path)

    total_jobs = len(list_info_attempt)

    # Chuyển cột job_link thành tập hợp để tăng hiệu suất so sánh
    job_links_all = set(list_info_all['job_link'])

    # Lọc ra các dòng chỉ có trong list_info_attempt nhưng không có trong list_info_all
    list_info_add = list_info_attempt[~list_info_attempt['job_link'].isin(job_links_all)]
    list_info_add_path = os.path.join(attempt_dir, "list_info_add.csv")

    new_jobs = len(list_info_add)

    # Lưu kết quả vào file list_info_add.csv
    list_info_add.to_csv(list_info_add_path, index=False)
    print(f"Đã lưu danh sách mới vào {list_info_add_path}")
    comparing_status = 'Success'
except :
    error_msg = f"Error in comparing process: "
    print('Error in comparing process')
    comparing_error_count += 1
    comparing_errors.append(error_msg)
    comparing_status = 'Failed'


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


def get_job_id(job_link):
    match = re.search(r'(\d+)-jv', job_link)
    if match:
        return match.group(1)  # Lấy số job_id
    return None


def detail_scraping(link):
    global detail_error_count, detail_errors

    try :
        print(f"Đang xử lý link: {link}")
        time.sleep(2)
        # job name
        print('job_name')
        try:
            time.sleep(2)
            name = driver.find_element(By.CSS_SELECTOR,'h1.sc-ab270149-0.hAejeW').text
        except:
            error_msg = f"Lỗi khi lấy job_name"
            detail_error_count += 1
            detail_errors.append(error_msg)
            print(f"Lỗi khi lấy job_name")
            name = None
        # job status
        print('job_status')
        try:
            time.sleep(2)
            job_status = driver.find_elements(By.CSS_SELECTOR,'span.sc-ab270149-0.ePOHWr')[0].text
        except:
            error_msg = f"Lỗi khi lấy job_status"
            detail_error_count += 1
            detail_errors.append(error_msg)
            print(f"Lỗi khi lấy job_status")
            job_status = "None"
        # company name and company href
        print('company_name and company_href')
        try:
            time.sleep(2)
            company_href = driver.find_element(By.CSS_SELECTOR,'a.sc-ab270149-0.egZKeY.sc-f0821106-0.gWSkfE').get_attribute("href")
            company_name = driver.find_element(By.CSS_SELECTOR,'a.sc-ab270149-0.egZKeY.sc-f0821106-0.gWSkfE').text
        except:
            error_msg = f"Lỗi khi lấy company_name and company_href"
            detail_error_count += 1
            detail_errors.append(error_msg)
            print(f"Lỗi khi lấy company_name and company_href")
            company_href = None
            company_name = None
        # city region
        try:
            time.sleep(2)
            city_region = driver.find_element(By.CSS_SELECTOR,'div.sc-2557ebc-1.ebdjLi span').text
        except:
            error_msg = f"Lỗi khi lấy city_region"
            detail_error_count += 1
            detail_errors.append(error_msg)
            print(f"Lỗi khi lấy city_region")
            city_region = None
        # salary
        try:
            salary = driver.find_elements(By.CSS_SELECTOR,'span.sc-ab270149-0.cVbwLK')[0].text
        except:
            error_msg = f"Lỗi khi lấy salary"
            detail_error_count += 1
            detail_errors.append(error_msg)
            print(f"Lỗi khi lấy salary")
            salary = None
        
        # scrape date
        scrape_date = datetime.now().isoformat()

        # job description
        try: 
            time.sleep(2)
            see_more_button = driver.find_element(By.CSS_SELECTOR,"button.sc-bd699a4b-0.kBdTlY.btn-info.btn-md.sc-1671001a-2.galMaY.clickable")
            print("Đã tìm thấy nút xem thêm")
            ActionChains(driver).move_to_element(see_more_button).click(see_more_button).perform()
            print("Đã click vào nút xem thêm")
            time.sleep(1)
            jd = driver.find_element(By.CSS_SELECTOR,'div.sc-1671001a-3.hmvhgA').text
            
        except:
            print("Không thể click vào nút xem thêm")
            try:
                jd = driver.find_element(By.CSS_SELECTOR,'div.sc-1671001a-3.hmvhgA').text
            except:
                error_msg = f"Lỗi khi lấy job description"
                detail_error_count += 1
                detail_errors.append(error_msg)
                print(f"Lỗi khi lấy job description")
                jd = None

        # job data
        job_data = {
            "job": {
                "company_name": company_name,
                "company_href": company_href,
                "job_name": name,
                "region": city_region,
                "job_status": job_status,
                "salary": salary,
                "scrape_date": scrape_date,
                "jd": jd
            }
        }
        print(job_data)

        list_info_all = pd.read_csv(list_info_all_path)
        list_info_done = pd.read_csv(list_info_done_path)

        # Thêm job_link vào list_info_all và list_info_done nếu chưa có
        if link not in list_info_all['job_link'].values:
            new_data_all = pd.DataFrame({"job_link": [link]})
            list_info_all = pd.concat([list_info_all, new_data_all], ignore_index=True)

        if link not in list_info_done['job_link'].values:
            new_data_done = pd.DataFrame({"job_link": [link]})
            list_info_done = pd.concat([list_info_done, new_data_done], ignore_index=True)

        # Lưu lại vào CSV
        list_info_all.to_csv(list_info_all_path, index=False)
        list_info_done.to_csv(list_info_done_path, index=False)
        print(f"Đã thêm dữ liệu vào list_info_all và list_info_done cho job_link: {link}")

        #detailview_attempt_path
        new_data = {
            "job_link": link,
            "job_name": job_data["job"]["job_name"],
            "job_status": job_data["job"]["job_status"],
            "region": job_data["job"]["region"],
            "company_name": job_data["job"]["company_name"],
            "company_href": job_data["job"]["company_href"],
            "job_status": job_data["job"]["job_status"],
            "scrape_date": job_data["job"]["scrape_date"],
            "jd": job_data["job"]["jd"]
        }
        detailview_attempt = pd.read_csv(detailview_attempt_path)
        detailview_attempt = pd.concat([detailview_attempt, pd.DataFrame([new_data])], ignore_index=True)
        detailview_attempt.to_csv(detailview_attempt_path, index=False)

        job_id = get_job_id(link)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        job_folder = os.path.join(detailview_dir, f"{job_id}_{timestamp}")
        os.makedirs(job_folder, exist_ok=True)

        html_file_path = os.path.join(job_folder, "page_source.html")
        with open(html_file_path, "w", encoding="utf-8") as html_file:
            html_file.write(driver.page_source)

        json_file_path = os.path.join(job_folder, "data.json")
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(job_data, json_file, indent=4, ensure_ascii=False)

        print(f"Đã lưu dữ liệu cho {job_id} vào {job_folder}")
        print(json.dumps(job_data, indent=4, ensure_ascii=False))
        return True
    except :
        error_msg = f"Lỗi khi xử lý link {link}"
        detail_error_count += 1
        detail_errors.append(error_msg)
        print(f"Lỗi khi xử lý link {link}")
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