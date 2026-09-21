# crawl-tin — VN Mobility News

Bộ lọc RSS tự động cho tin xe cộ, giao thông, tai nạn, đường sắt, tàu thuyền/du thuyền và các thương hiệu xe.

## Cài đặt
Upload toàn bộ file và thư mục trong gói này vào root của repository GitHub.

Sau đó:
1. Mở tab **Actions**.
2. Chọn **Build mobility RSS**.
3. Chọn **Run workflow** để chạy lần đầu.
4. Sau khi chạy thành công, repo sẽ xuất hiện `feed.xml`.

RSS để thêm vào Inoreader:
https://raw.githubusercontent.com/duongww-maker/crawl-tin/main/feed.xml

Workflow được đặt lịch 15 phút/lần.

## Chỉnh nguồn và từ khóa
- `sources.json`: danh sách RSS nguồn.
- `keywords.json`: từ khóa chủ đề và thương hiệu.
