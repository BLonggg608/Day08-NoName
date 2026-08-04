"""
Task 1 — Thu thập văn bản chính sách/quy định dịch vụ đại học.

Hướng dẫn:
    1. Tìm tối thiểu 3 văn bản chính sách (PDF/DOCX) từ trang công khai của một trường đại học.
    2. Tải về và lưu vào data/landing/legal/
    3. Đặt tên file rõ ràng, không dấu, mô tả đúng nội dung.
"""

import requests
from pathlib import Path

# Xác định đường dẫn tương đối tới thư mục chứa dữ liệu
DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Thư mục đã sẵn sàng: {DATA_DIR}")


def download_file(url: str, filename: str):
    """
    Tải file từ URL và lưu vào hệ thống.
    Sử dụng headers giả lập trình duyệt để tránh bị chặn 403 Forbidden.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    filepath = DATA_DIR / filename
    
    try:
        print(f"⏳ Đang tải: {filename}...")
        # Stream=True giúp tải an toàn các file PDF dung lượng lớn
        response = requests.get(url, headers=headers, stream=True, timeout=15)
        response.raise_for_status() # Báo lỗi nếu tải thất bại (404, 403...)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"  ✅ Đã lưu: {filepath}")
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Lỗi khi tải {filename}: {e}")
        print("  💡 Hướng xử lý: Thử tìm một URL PDF khác hoặc tải file thủ công bằng trình duyệt rồi copy vào thư mục data/landing/legal/")


if __name__ == "__main__":
    setup_directory()
    
    # Danh sách 3 tài liệu chính sách (direct link tới file PDF)
    # Lưu ý: Tên file phải viết thường, không dấu, ngăn cách bằng gạch ngang
    documents = [
        {
            "url": "https://www.bing.com/ck/a?!&&p=9a04e44296c5f305ada01666aefa3bbf32ed3b3b63c1c1231bb2b7bb75dea808JmltdHM9MTc4NTcxNTIwMA&ptn=3&ver=2&hsh=4&fclid=07e7bb2b-00e9-615d-30c7-adb2018f60b4&psq=rmit-university-vietnam-scholarship-terms-and-conditions.pdf&u=a1aHR0cHM6Ly93d3cucm1pdC5lZHUudm4vY29udGVudC9kYW0vcm1pdC92bi9lbi9hc3NldHMtZm9yLXByb2R1Y3Rpb24vZG9jdW1lbnRzL3BkZnMvc3R1ZHktYXQtcm1pdC9zY2hvbGFyc2hpcHMvZW5nbGlzaC1wZGYvcm1pdC11bml2ZXJzaXR5LXZpZXRuYW0tc2Nob2xhcnNoaXAtdGVybXMtYW5kLWNvbmRpdGlvbnMucGRm",
            "filename": "rmit-university-vietnam-scholarship-terms-and-conditions.pdf"
        },
        {
            "url": "https://www.bing.com/ck/a?!&&p=fb655db6e306e450e96966ea13e10a10b3fed29e5e77d699c55317c70f0691e3JmltdHM9MTc4NTcxNTIwMA&ptn=3&ver=2&hsh=4&fclid=07e7bb2b-00e9-615d-30c7-adb2018f60b4&psq=student-fees-and-charges-guide-06-2026.pdf&u=a1aHR0cHM6Ly93d3cucm1pdC5lZHUudm4vY29udGVudC9kYW0vcm1pdC92bi9lbi9hc3NldHMtZm9yLXByb2R1Y3Rpb24vZG9jdW1lbnRzL3BkZnMvc3R1ZHktYXQtcm1pdC90dWl0aW9uLWZlZXMvc3R1ZGVudC1mZWVzLWFuZC1jaGFyZ2VzLWd1aWRlLTA2LTIwMjYucGRm",
            "filename": "student-fees-and-charges-guide-06-2026.pdf"
        },
        {
            "url": "https://www.bing.com/ck/a?!&&p=65d630ff5da6e9b5a7a58f00065094a0985fc45d6eb6a5874f59adab2d7baeeeJmltdHM9MTc4NTcxNTIwMA&ptn=3&ver=2&hsh=4&fclid=07e7bb2b-00e9-615d-30c7-adb2018f60b4&psq=brochure-for-international-students-vi.pdf&u=a1aHR0cHM6Ly93d3cucm1pdC5lZHUudm4vYXNzZXRzL3ZuL2VuL2Fzc2V0cy1mb3ItcHJvZHVjdGlvbi9kb2N1bWVudHMvcGRmcy9zdHVkeS1hdC1ybWl0L2ludGVybmF0aW9uYWwtc3R1ZGVudHMvaW50ZXJuYXRpb25hbC1zdHVkZW50LWd1aWRlLTIwMjYucGRm",
            "filename": "international-student-guide-2026.pdf"
        }
    ]
    
    print("\n🚀 BẮT ĐẦU TẢI DỮ LIỆU CHÍNH SÁCH...")
    print("-" * 60)
    
    for doc in documents:
        download_file(doc["url"], doc["filename"])
        
    print("-" * 60)
    print("🎉 Hoàn thành Task 1! Hãy mở thư mục data/landing/legal/ để kiểm tra file.")