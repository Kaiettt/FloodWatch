"""
Script to fix duplicate subscription issue
Xóa các subscription cũ và tạo lại
"""
import requests
import time

ORION_URL = "http://localhost:1026/ngsi-ld/v1/subscriptions"

def delete_subscription(sub_id: str) -> bool:
    """Xóa một subscription cụ thể"""
    try:
        # URL encode the subscription ID
        delete_url = f"{ORION_URL}/{sub_id}"
        response = requests.delete(delete_url)
        
        if response.status_code in (204, 404):
            print(f"✓ Đã xóa: {sub_id}")
            return True
        else:
            print(f"✗ Không xóa được: {sub_id} (Status: {response.status_code})")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Lỗi khi xóa {sub_id}: {str(e)}")
        return False

def get_all_subscriptions():
    """Lấy danh sách tất cả subscriptions"""
    try:
        response = requests.get(ORION_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Lỗi khi lấy danh sách subscriptions: {response.status_code}")
            return []
    except Exception as e:
        print(f"Lỗi kết nối Orion-LD: {str(e)}")
        return []

def fix_duplicate_subscriptions():
    """Xóa các subscription trùng lặp"""
    print("=" * 60)
    print("BẮT ĐẦU SỬA LỖI SUBSCRIPTION")
    print("=" * 60)
    
    # Lấy danh sách subscriptions
    print("\n1. Đang lấy danh sách subscriptions...")
    subscriptions = get_all_subscriptions()
    
    if not subscriptions:
        print("⚠ Không tìm thấy subscription nào hoặc không kết nối được Orion-LD")
        print("\nVui lòng kiểm tra:")
        print("  - Docker containers đang chạy: docker ps")
        print("  - Orion-LD có sẵn tại: http://localhost:1026")
        return
    
    print(f"   Tìm thấy {len(subscriptions)} subscriptions")
    
    # Hiển thị danh sách
    print("\n2. Danh sách subscriptions hiện tại:")
    for sub in subscriptions:
        sub_id = sub.get('id', 'Unknown')
        sub_name = sub.get('name', 'No name')
        entity_type = sub.get('entities', [{}])[0].get('type', 'Unknown')
        print(f"   - {sub_id}")
        print(f"     Name: {sub_name}, Entity: {entity_type}")
    
    # Hỏi có muốn xóa không
    print("\n3. Bạn có muốn xóa TẤT CẢ subscriptions và tạo lại không?")
    print("   Điều này sẽ giải quyết vấn đề 'Already exists'")
    confirm = input("   Nhập 'yes' để tiếp tục: ").strip().lower()
    
    if confirm != 'yes':
        print("\n❌ Đã hủy. Không có thay đổi nào.")
        return
    
    # Xóa từng subscription
    print("\n4. Đang xóa subscriptions...")
    deleted_count = 0
    for sub in subscriptions:
        sub_id = sub.get('id')
        if sub_id and delete_subscription(sub_id):
            deleted_count += 1
            time.sleep(0.2)  # Đợi một chút giữa các lần xóa
    
    print(f"\n✓ Đã xóa {deleted_count}/{len(subscriptions)} subscriptions")
    
    # Hướng dẫn tạo lại
    print("\n" + "=" * 60)
    print("HOÀN THÀNH! Bây giờ bạn cần:")
    print("=" * 60)
    print("\n1. Khởi động lại subscription container:")
    print("   docker restart floodwatch-subscription")
    print("\n2. Hoặc chạy script subscription thủ công:")
    print("   python subscription/subscription_main.py")
    print("\n3. Kiểm tra logs:")
    print("   docker logs floodwatch-subscription")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    fix_duplicate_subscriptions()
