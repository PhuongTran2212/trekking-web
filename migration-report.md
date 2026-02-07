# Migration Report – TrekViet Design System

## 1. File HTML đã quét

- `templates/base.html`
- `templates/admin_base.html`
- `templates/admin/dashboard.html`
- `templates/home.html`
- `templates/articles/*.html`
- `templates/community/*.html`
- `templates/knowledge/*.html`
- `templates/post/*.html`
- `templates/report/*.html`
- `templates/partials/_header_user.html`
- `templates/partials/_header_guest.html`
- `templates/partials/_header_admin.html`
- `templates/partials/_sidebar_admin.html`
- `templates/partials/_footer.html`
- `templates/partials/_form_field_class_filter*.html`
- `templates/partials/comment.html`
- `accounts/templates/accounts/*.html`
- `trips/templates/trips/*.html`
- `trips/templates/admin/trips/*.html`
- `treks/templates/treks/*.html`
- `treks/templates/admin/treks/*.html`
- `core/templates/admin/system_config.html`
- `gamification/templates/gamification/*.html`

## 2. Phân tích & vấn đề chính

- **Màu sắc**: nhiều palette khác nhau (`--th-*`, `--trek-*`, `--primary-color` trong admin) và màu inline (#28a745, #ffc107, #dc3545, #666, #333, #ddd...).  
  → Đã chuẩn hóa về `variables.css` với `--color-primary`, `--color-primary-dark`, `--color-primary-light`, `--color-neutral*`.

- **Radius & shadow**: card/btn dùng 6px/8px/10px/12px/16px và nhiều shadow khác nhau.  
  → Chuẩn: `--radius-md: 12px` (mặc định), `--shadow-md: 0 4px 18px rgba(0,0,0,0.08)` làm shadow mặc định.

- **Buttons**: `.btn`, `.th-btn`, `.trek-btn`, `.btn-primary/secondary/outline/link/danger` không đồng bộ padding/màu.  
  → Đã định nghĩa `.btn` + modifiers `.btn--primary`, `.btn--secondary`, `.btn--outline`, `.btn--ghost`, `.btn--danger`, `.btn--sm`, `.btn--full` trong `components/buttons.css`.

- **Cards**: nhiều loại card (Bootstrap `.card`, `trek-card`, `trip-card`, `badge-card`, `card-modern`, `stat-card`, `rich-trip-card`).  
  → Đã chuẩn hoá `.card`, `.card--elevated`, `.card--interactive` trong `components/cards.css`.

- **Forms**: `form-group`, `trek-form-group`, `form-label`, `form-label-modern`, inline-style cho spacing font-size.  
  → Gom về `.form-field`, `.form-field__label`, `.form-control`, `.form-field__error`, `.form-field__help` trong `components/forms.css`.

- **Navbar/Header/Footer**: 
  - Header user/guest dùng `.th-*` với CSS inline lớn, palette riêng.  
  - Footer dùng `.site-footer` + CSS inline với variables riêng.  
  → Đã tạo `layout/header.css`, `layout/footer.css`, dùng `.site-header`, `.site-brand`, `.nav*`, `.site-footer*`.

- **Inline-style**: xuất hiện nhiều ở `home.html`, `xoa_bai_viet.html`, `knowledge_list.html`, `admin_report_detail.html`, `system_config.html`, `profile_detail.html`, `trip_card.html`…  
  → Đề xuất thay bằng utilities (`.u-mt-16`, `.u-text-center`, `.u-flex`, `.u-gap-8`, `.u-p-12`, `.u-pt-24`, `.u-w-full`) và class component (`.card`, `.btn`, `.badge`).

## 3. Design System mới (CSS đã tạo)

### 3.1. Base

- `static/css/base/reset.css` – reset nhẹ, box-sizing, body, link, table, form, helper `.visually-hidden`.
- `static/css/base/variables.css` – biến màu, typography, spacing (4/8/12/16/24/32), radius, shadow, transition, breakpoints (1200/992/768/576).
- `static/css/base/typography.css` – heading `.h1`–`.h6`, `.text-body`, `.text-muted`, `.text-sm`, `.text-xs`, `.text-bold`, `.text-semibold`, `.text-light`.

### 3.2. Layout

- `static/css/layout/grid.css` – `.container`, `.page-section`, `.row`, `.col-*`, layout `.layout-main-with-sidebar`.
- `static/css/layout/header.css` – `.site-header`, `.site-header__inner`, `.site-brand`, `.nav`, `.nav__item`, `.nav__link`, `.nav__dropdown`, `.nav__dropdown-menu`, `.nav__dropdown-item`.
- `static/css/layout/footer.css` – `.site-footer`, `.site-footer__inner`, `.footer-grid`, `.footer-brand`, `.footer-column__title`, `.footer-links`, `.footer-social__item`, `.footer-bottom`.

### 3.3. Components

- `static/css/components/buttons.css` – `.btn`, `.btn--primary`, `.btn--secondary`, `.btn--outline`, `.btn--ghost`, `.btn--danger`, `.btn--sm`, `.btn--lg`, `.btn--full`, `.btn--link`.
- `static/css/components/cards.css` – `.card`, `.card--elevated`, `.card--interactive`, `.card__header`, `.card__title`, `.card__subtitle`, `.card__body`, `.card__footer`, `.card-grid`.
- `static/css/components/forms.css` – `.form-field`, `.form-field__label`, `.form-control`, `.input`, `.input--textarea`, `.form-field--error`, `.form-field__error`, `.form-field__help`.
- `static/css/components/modal.css` – `.modal-overlay`, `.modal-overlay.is-visible`, `.modal`, `.modal__header`, `.modal__title`, `.modal__body`, `.modal__footer`.
- `static/css/components/nav.css` – `.nav-tabs`, `.nav-tabs__item`, `.nav-tabs__item--active`, `.sidebar`, `.sidebar__nav`, `.sidebar__item`, `.sidebar__link`, `.sidebar__link--active`.
- `static/css/components/table.css` – `.table`, `.table--striped`, `.table--hover`, `.table-row-card`.

### 3.4. Pages

- `static/css/pages/home.css` – `.home-hero`, `.home-hero__title`, `.home-hero__subtitle`.
- `static/css/pages/cung_duong_list.css` – `.cungduong-page`, `.cungduong-layout`, `.cungduong-filter*`, `.cungduong-grid`, `.cungduong-card*`, `.cungduong-pagination`.
- `static/css/pages/trip_hub.css` – `.trip-hub`, `.trip-hub__layout`, `.trip-hub__sidebar`, `.trip-filter*`, `.trip-grid`.
- `static/css/pages/community_list.css` – `.community-list`, `.community-list__header`, `.community-post-card*`, `.pagination`, `.pagination__item`, `.pagination__item--active`.

### 3.5. Global & Utilities

- `static/css/global.css`:
  - Import toàn bộ base/layout/components/pages.
  - Utilities:
    - Spacing: `.u-mt-16`, `.u-mb-16`, `.u-p-12`, `.u-pt-24`, `.u-px-16`.
    - Layout: `.u-flex`, `.u-flex-center`, `.u-justify-between`, `.u-gap-8`.
    - Text/width: `.u-text-center`, `.u-text-muted`, `.u-w-full`.

## 4. Mapping class cũ → class mới (tóm tắt)

### Buttons

- `.btn.btn-primary` → `.btn btn--primary`
- `.btn.btn-secondary` → `.btn btn--secondary`
- `.btn.btn-outline` / `.btn.btn-outline-secondary` → `.btn btn--outline`
- `.btn.btn-link` → `.btn btn--link`
- `.btn.btn-danger` → `.btn btn--danger`
- `.th-btn-primary` → `.btn btn--primary`
- `.th-btn-ghost` → `.btn btn--ghost`
- `.trek-btn.trek-btn-primary` → `.btn btn--primary`
- `.trek-btn.trek-btn-outline` → `.btn btn--outline`

### Cards

- `.trek-card` → `.card card--elevated card--interactive`
- `.trip-card` → `.card card--elevated card--interactive`
- `.badge-card` → `.card card--elevated`
- `.card-modern`, `.stat-card`, `.rich-trip-card` → `.card card--elevated`

### Form

- `.form-group` → `.form-field`
- `.trek-form-group` → `.form-field`
- `.form-label`, `.trek-form-label`, `.form-label-modern` → `.form-field__label`
- `.form-text` → `.form-field__help`
- `.error-text` → `.form-field__error`

### Header / Navbar `.th-*` (gợi ý)

- `.th-header` → `.site-header`
- `.th-container` → `.site-header__inner`
- `.th-nav` → `.nav`
- `.th-nav-list` → `.nav`
- `.th-nav-item` → `.nav__item`
- `.th-nav-link` → `.nav__link`
- `.th-dropdown` → `.nav__dropdown`
- `.th-dropdown-menu` → `.nav__dropdown-menu`
- `.th-dropdown-item` → `.nav__dropdown-item`

### Footer

- `.site-footer` (cũ) → `.site-footer` (mới, giữ tên)
- `.footer-content` → `.footer-grid`
- `.footer-brand` → `.footer-brand`
- `.footer-column` → sử dụng `.footer-column__title` + `.footer-links` bên trong.

### Badge (đề xuất)

- `.badge.badge-success` → `.badge badge--success` (cần thêm file badge.css nếu muốn tách riêng).
- `.badge.badge-info` → `.badge badge--info`
- `.status-badge`, `.badge-level`, `.bg-st-*` → `.badge badge--pill` + modifier màu tuỳ trạng thái.

## 5. Thay đổi đã thực hiện trong code

### 5.1. Thêm link tới `global.css`

- `templates/base.html`:
  - Thêm:
    ```html
    <link rel="stylesheet" href="{% static 'css/global.css' %}">
    ```
  - Giữ lại một bản Bootstrap và `css/styles.css` để không vỡ layout cũ trong giai đoạn migrate.

- `templates/admin_base.html`:
  - Thêm:
    ```html
    <link rel="stylesheet" href="{% static 'css/global.css' %}">
    ```
  - Vẫn giữ Bootstrap + `css/styles.css` + FontAwesome.

### 5.2. File CSS mới đã được tạo

- `static/css/base/reset.css`
- `static/css/base/variables.css`
- `static/css/base/typography.css`
- `static/css/layout/grid.css`
- `static/css/layout/header.css`
- `static/css/layout/footer.css`
- `static/css/components/buttons.css`
- `static/css/components/cards.css`
- `static/css/components/forms.css`
- `static/css/components/modal.css`
- `static/css/components/nav.css`
- `static/css/components/table.css`
- `static/css/pages/home.css`
- `static/css/pages/cung_duong_list.css`
- `static/css/pages/trip_hub.css`
- `static/css/pages/community_list.css`
- `static/css/global.css`

## 6. Hướng dẫn dev áp dụng

1. **Đảm bảo static đã build đúng**  
   - Các file CSS đã nằm trong `static/css/...`. Khi chạy server Django với `DEBUG=True`, static sẽ được serve tự động.  
   - Khi deploy, cần chạy collectstatic như bình thường.

2. **Dùng dần class mới song song với class cũ**  
   - Không xoá ngay CSS cũ (`styles.css`, các `<style>` block trong template) để tránh vỡ UI.  
   - Khi sửa 1 template, ưu tiên:
     - Thay inline-style bằng utilities (`.u-*`) và component class.
     - Thay `.btn btn-primary` → `.btn btn--primary`.  
     - Thay `.trek-card` → `.card card--elevated card--interactive`, v.v.

3. **Ví dụ thay đổi HTML (mẫu)**

- Home hero:

  Trước:

  ```html
  <div style="text-align: center; padding: 50px;">
      <h1>Chào mừng đến với TrekViet</h1>
      <p>Nơi kết nối những tâm hồn đam mê khám phá.</p>
  </div>
  ```

  Sau:

  ```html
  <div class="home-hero u-text-center u-pt-24 u-px-16">
      <h1 class="home-hero__title">Chào mừng đến với TrekViet</h1>
      <p class="home-hero__subtitle">Nơi kết nối những tâm hồn đam mê khám phá.</p>
  </div>
  ```

- Button cơ bản:

  Trước:

  ```html
  <a href="..." class="btn btn-primary">Tạo bài viết</a>
  ```

  Sau:

  ```html
  <a href="..." class="btn btn--primary">Tạo bài viết</a>
  ```

4. **Quy trình refactor đề xuất**

- Bước 1: Kiểm tra static load `css/global.css` đúng trên cả frontend & admin.  
- Bước 2: Migrate theo module:
  - `home` → `treks` (`cung_duong_list`) → `trips` (`trip_hub`) → `community` → `knowledge` → `accounts` → admin.  
- Bước 3: Sau khi toàn bộ template đã dùng class mới và không còn phụ thuộc vào CSS inline/`styles.css`, có thể dọn dần:
  - Xoá các block `<style>` lớn trong template (đưa logic vào file `.css` riêng nếu cần).
  - Rút gọn/loại bỏ `static/css/styles.css`.

## 7. Ghi chú

- Các template sử dụng Django template tags (`{% %}`, `{{ }}`) không bị thay đổi; mọi snippet after vẫn giữ nguyên block/template tags.  
- Thiết kế mới ưu tiên flexbox/grid, tránh dùng `!important`, dùng biến CSS từ `variables.css`.  
- Nếu cần mở rộng cho từng trang (vd. profile, knowledge detail), nên tạo thêm file trong `static/css/pages/` và import từ `global.css`.


