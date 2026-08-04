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
            "url": "https://www.rmit.edu.vn/content/dam/rmit/vn/en/assets-for-production/documents/students/student-fees/2024-tuition-fees/2024-tuition-fees-vn.pdf",
            "filename": "tuition-fees-policy.pdf"
        },
        {
            "url": "https://www.rmit.edu.vn/content/dam/rmit/vn/en/assets-for-production/documents/study-with-us/scholarships/2024-scholarships-terms-and-conditions.pdf",
            "filename": "scholarship-terms-and-conditions.pdf"
        },
        {
            "url": "https://www.rmit.edu.vn/content/dam/rmit/vn/en/assets-for-production/documents/students/student-services/accommodation/rmit-accommodation-rules.pdf",
            "filename": "accommodation-rules.pdf"
        }
    ]
    
    print("\n🚀 BẮT ĐẦU TẢI DỮ LIỆU CHÍNH SÁCH...")
    print("-" * 60)
    
    for doc in documents:
        download_file(doc["url"], doc["filename"])
        
    print("-" * 60)
    print("🎉 Hoàn thành Task 1! Hãy mở thư mục data/landing/legal/ để kiểm tra file.")