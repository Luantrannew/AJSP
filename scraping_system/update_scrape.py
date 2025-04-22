import os
import subprocess
import sys
import time

def run_script(script_path):
    """
    Chạy một file Python và chờ cho đến khi nó hoàn thành
    """
    print(f"\n{'='*50}")
    print(f"Đang chạy: {script_path}")
    print(f"{'='*50}\n")
    
    start_time = time.time()
    
    try:
        # Sử dụng subprocess để chạy script Python
        # Đảm bảo rằng output được hiển thị trực tiếp
        result = subprocess.run([sys.executable, script_path], 
                               check=True,
                               text=True)
        
        execution_time = time.time() - start_time
        print(f"\n{'='*50}")
        print(f"Đã hoàn thành: {script_path}")
        print(f"Thời gian thực thi: {execution_time:.2f} giây")
        print(f"{'='*50}\n")
        return True
        
    except subprocess.CalledProcessError as e:
        execution_time = time.time() - start_time
        print(f"\n{'='*50}")
        print(f"Lỗi khi chạy: {script_path}")
        print(f"Mã lỗi: {e.returncode}")
        print(f"Thời gian thực thi: {execution_time:.2f} giây")
        print(f"{'='*50}\n")
        return False
    
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"\n{'='*50}")
        print(f"Lỗi không mong đợi khi chạy: {script_path}")
        print(f"Lỗi: {str(e)}")
        print(f"Thời gian thực thi: {execution_time:.2f} giây")
        print(f"{'='*50}\n")
        return False

def main():
    # Danh sách các script cần chạy theo thứ tự
    scripts = [
        r"C:\working\job_rcm\job_rcm_code\job_scraping\facebook\main.py",
        r"C:\working\job_rcm\job_rcm_code\job_scraping\linkedin\main.py",
        r"C:\working\job_rcm\job_rcm_code\job_scraping\website\vietnamwork\main.py",
        r"C:\working\job_rcm\job_rcm_code\job_scraping\data_preprocessing\update_code\facebook_preprocessed\main.py",
        r"C:\working\job_rcm\job_rcm_code\job_scraping\\data_preprocessing\update_code\linkedin_preprocessed\main.py",
        r"C:\working\job_rcm\job_rcm_code\job_scraping\\data_preprocessing\update_code\vnw_proprocessed\main.py",
        r"C:\working\job_rcm\job_rcm_code\job_scraping\\data_preprocessing\update_code\intergrate\main.py",
        r"C:\working\job_rcm\job_rcm_code\job_scraping\scraping_system\drive_upload.py",
    ]
    
    total_start_time = time.time()
    print(f"Bắt đầu chạy {len(scripts)} scripts...")
    
    success_count = 0
    
    # Chạy từng script một theo thứ tự
    for i, script_path in enumerate(scripts, 1):
        print(f"Script {i}/{len(scripts)}")
        
        # Kiểm tra xem file có tồn tại không
        if not os.path.exists(script_path):
            print(f"Lỗi: File không tồn tại: {script_path}")
            continue
            
        # Chạy script
        success = run_script(script_path)
        if success:
            success_count += 1
    
    total_time = time.time() - total_start_time
    print(f"\n{'='*50}")
    print(f"Kết quả: {success_count}/{len(scripts)} scripts đã chạy thành công")
    print(f"Tổng thời gian: {total_time:.2f} giây")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()