# openinfra

## Thiết lập nhanh

1) Cài đặt phụ thuộc:
```
pip install -r backend/requirements.txt
cd frontend && npm install
```

2) Cấu hình môi trường:
- Sao chép `backend/.env.example` thành `backend/.env` và điều chỉnh khi cần (MongoDB, JWT secret, admin mặc định).
- Sao chép `infra/.env.example` nếu chạy docker-compose.
- Frontend: `frontend/.env.example` chứa `VITE_BASE_API_URL` và `VITE_LEADERBOARD_URL`.

3) Tạo tài khoản admin (JWT):
```
python backend/scripts/create_superuser.py
```
Script sẽ đọc giá trị `ADMIN_DEFAULT_USERNAME` và `ADMIN_DEFAULT_PASSWORD` trong `.env` (giá trị mẫu trong `.env.example` chỉ mang tính tham khảo, bạn nên đặt mật khẩu mạnh của riêng mình). Script sẽ xoá sạch bản ghi admin cũ rồi tạo lại tài khoản này.

4) Chạy ứng dụng:
- Backend: `uvicorn app.main:app --reload` (thư mục backend).
- Frontend: `npm run dev` (thư mục frontend).

## Đăng nhập admin
- Trang đăng nhập: `/admin/login`
- Tài khoản mặc định: lấy từ `.env` (tự đặt). Giá trị mẫu trong `.env.example` chỉ để tham khảo.
- Access token được lưu tại `localStorage` khóa `access-token`.
