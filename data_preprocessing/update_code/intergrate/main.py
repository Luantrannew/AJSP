import pandas as pd
import os
from datetime import datetime
import uuid
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
    return f"INPR_{timestamp}_{random_suffix}_{scraping_type}"

# Function to write a start log entry
def write_start_log(log_id, scraping_type, keywords=""):
    sheet.append_row([
            log_id,
            '',
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
            '',
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


preprocess_log_id = generate_log_id("Intergrate_preprocess")
preprocess_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
scraping_type = "Intergrate_preprocess"
# Ghi log bắt đầu
write_start_log(preprocess_log_id, scraping_type, keywords="Intergrate_preprocess")

# Đường dẫn
output_path = r'C:\working\job_rcm\data\preprocessed\final.csv'

fb_path = r'C:\working\job_rcm\data\preprocessed\facebook\preprocessed_data.csv'
ld_path = r'C:\working\job_rcm\data\preprocessed\linkedin\preprocessed_data.csv'
vnw_path = r'C:\working\job_rcm\data\preprocessed\vietnamwork\preprocessed_data.csv'

# Đọc dữ liệu
facebook_df = pd.read_csv(fb_path)
ld_df = pd.read_csv(ld_path)
vnw_df = pd.read_csv(vnw_path)

# Chuẩn hóa các DataFrame
# Facebook
facebook_df['source'] = 'facebook'
facebook_df = facebook_df.rename(columns={
    'post_href': 'job_link',
    'content': 'description'
})
facebook_df['hr_id'] = facebook_df.get('hr_id', None)
facebook_df['post_date'] = facebook_df.get('post_date', None)
facebook_df['company_name'] = None
facebook_df['company_href'] = None
facebook_df['job_name'] = None
facebook_df['salary'] = None
facebook_df['region'] = None
facebook_df['job_status'] = None
facebook_df['jd'] = None

# LinkedIn
ld_df['source'] = 'linkedin'
ld_df = ld_df.rename(columns={
    'job_link': 'job_link',
    'company_name': 'company_name',
    'company_href': 'company_href',
    'job_name': 'job_name',
    'region': 'region',
    'job_status': 'job_status',
    'scrape_date': 'scrape_date',
    'hr_id': 'hr_id',
    'jd': 'jd'
})
ld_df['description'] = None
ld_df['salary'] = None
ld_df['post_date'] = None

# VietnamWorks
vnw_df['source'] = 'vietnamwork'
vnw_df = vnw_df.rename(columns={
    'job_link': 'job_link',
    'company_name': 'company_name',
    'company_href': 'company_href',
    'job_name': 'job_name',
    'salary': 'salary',
    'region': 'region',
    'job_status': 'job_status',
    'scrape_date': 'scrape_date',
    'hr_id': 'hr_id',
    'jd': 'jd'
})
vnw_df['description'] = None
vnw_df['post_date'] = None

# Danh sách cột chuẩn hóa
columns = [
    'source', 'job_link', 'hr_id', 'company_name', 'company_href', 
    'job_name', 'salary', 'region', 'job_status','post_date', 'scrape_date', 'jd', 'description'
]

# Thêm cột thiếu và sắp xếp thứ tự
facebook_df = facebook_df.reindex(columns=columns)
ld_df = ld_df.reindex(columns=columns)
vnw_df = vnw_df.reindex(columns=columns)

# Gộp các DataFrame
merged_df = pd.concat([facebook_df, ld_df, vnw_df], ignore_index=True)

# Xuất dữ liệu
merged_df.to_csv(output_path, index=False, encoding='utf-8')
print(f"Dữ liệu đã được lưu vào: {output_path}")
msg = f"Dữ liệu đã được lưu"

# Ghi log kết thúc
write_end_log(
    log_id=preprocess_log_id,
    scraping_type=scraping_type,
    start_time=preprocess_start_time,
    status="Completed",
    total_keywords=0,
    total_jobs=0,
    new_jobs=0,
    error_count=0,
    error_details="",
    keywords="Intergrate_preprocess"
)