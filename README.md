# TrekViet - Vietnam Trekking Management System

![TrekViet Banner](./docs/images/banner.png)
*A comprehensive platform connecting Vietnam's trekking community*

## 📖 Overview

**TrekViet** is a full-featured Django web platform designed to connect the trekking and mountaineering community in Vietnam. The system provides comprehensive tools for managing trekking routes, organizing trips, sharing experiences, and building an active outdoor enthusiast community.

## ✨ Key Features

### 🗺️ Trekking Route Management

- **Comprehensive route information**: Name, location, distance, elevation gain, estimated time, difficulty level
- **Media management system**: Upload and manage photos/videos for each route with dedicated cover images
- **Rating & review system**: Users can rate routes, write reviews, and upload accompanying photos
- **Map integration**: GeoJSON data support for route visualization
- **Equipment suggestions**: Recommended gear list for each route
- **Approval workflow**: Admin approval/rejection system for user-submitted routes
- **Advanced filtering**: By province, difficulty level, best season

### 🎒 Trip Organization

- **Create and manage trips**: 
  - Select base route and customize itinerary
  - Set participant limit, estimated cost, meeting point
  - Support for public or private mode with invite codes
- **Member management**:
  - Join request and approval system
  - Role assignment (Trip Leader, Member)
  - Participation status tracking
- **Real-time group chat**:
  - Text messaging with reply support
  - Upload photos, videos, attachments
  - Like/dislike system for messages
- **Detailed timeline**: Daily schedule planning with specific time slots
- **Dynamic status system**: Pending Approval, Recruiting, Full, Ongoing, Completed

### 👥 Community

- **Community posts**:
  - Create posts with title, content, and multimedia
  - Tag association and trip linking
  - Upvote/downvote system
  - Comments and nested replies
- **Moderation system**: Admin approval before public display
- **Report violations**: Users can report inappropriate content

### 🏆 Gamification

- **Diverse badge system** with 14 achievement types:
  - Number of trips participated/organized
  - Posts, comments, messages count
  - Total distance, elevation gained
  - Provinces visited
  - Difficulty level challenges
- **Auto-award system**: Automatically checks and awards badges when conditions are met
- **Achievement profile**: Display all earned badges on user profile

### 📚 Knowledge Base & Guides

- **Tutorial articles**: 
  - Categorization by topics
  - Rich TinyMCE editor support
  - Thumbnail images for each article
- **Approval workflow**: Admin moderation before publishing

### 👤 Account Management

- **Detailed user profiles**:
  - Basic information: name, email, phone number
  - Date of birth, gender, province/city
  - Avatar image
  - Accumulated reward points
- **Personal equipment management**:
  - List of owned trekking gear
  - Category-based organization
  - Quantity and condition notes
- **Interests and tags**: Subscribe to favorite tags

### 🔔 Notification System

- **Real-time notifications**: Updates about trips, comments, approvals
- **Read/unread status**: Manage notification states
- **Direct links**: Click to navigate to related content

### 🛡️ Reporting & Admin System

- **Violation reports**: 
  - Generic Foreign Key support for reporting multiple object types
  - Status management: New, Processing, Resolved
- **Admin dashboard**:
  - System overview statistics
  - User management
  - Approve routes, trips, posts
  - Handle violation reports
- **Base data management**:
  - Provinces, difficulty levels, equipment types
  - Tags and hashtags
  - Article categories

## 🏗️ System Architecture

### App Structure

```
trekking_web/
├── accounts/          # User accounts and profile management
├── articles/          # Knowledge articles and guides
├── community/         # Community posts and comments
├── core/              # Shared models (Provinces, Tags, Equipment, Difficulty)
├── gamification/      # Badge and achievement system
├── knowledge/         # Trekking knowledge (legacy)
├── post/              # Post management interface
├── report_admin/      # Violation report management
├── treks/             # Trekking route management
├── trips/             # Trip organization and management
└── user_admin/        # User administration
```

### Database Schema Highlights

**11 core models** tightly integrated:
- `CungDuongTrek` - Route information with GeoJSON, media, ratings
- `ChuyenDi` - Trips with timeline, members, chat
- `CongDongBaiViet` - Community posts with media, upvotes, comments
- `GameHuyHieu` - Badges with flexible condition logic
- `TaiKhoanHoSo` - User profiles with equipment and preferences

## 🚀 Technologies Used

### Backend
- **Django 4.2.23** - Main web framework
- **MySQL** - Database (mysqlclient 2.2.7)
- **Python 3.x**

### Frontend & UI
- **TinyMCE** - Rich text editor for articles
- **Bootstrap** - Base CSS framework
- **Custom Design System** - TrekViet design system with variables, components
- **Font Awesome** - Icon library

### Third-party Libraries
- **Pillow 11.3.0** - Image processing
- **django-taggit** - Tagging system
- **requests 2.32.5** - HTTP client

## 📦 Installation

### System Requirements

- Python 3.8+
- MySQL 5.7+ or MariaDB
- XAMPP/WAMP (or standalone MySQL server)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd trekking_web
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Database

1. Create MySQL database:
```sql
CREATE DATABASE trekking_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Update database settings in `trekking_project/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'trekking_db',
        'USER': 'root',
        'PASSWORD': '',  # Your MySQL password
        'HOST': '127.0.0.1',
        'PORT': '3307',  # Change if different MySQL port
    }
}
```

### Step 5: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 7: Collect Static Files

```bash
python manage.py collectstatic
```

### Step 8: Run Development Server

```bash
python manage.py runserver
```

Access: `http://127.0.0.1:8000`

## 📂 Directory Structure

```
trekking_web/
├── static/
│   ├── css/
│   │   ├── base/           # Reset, variables, typography
│   │   ├── layout/         # Grid, header, footer
│   │   ├── components/     # Buttons, cards, forms, modals
│   │   ├── pages/          # Page-specific styles
│   │   └── global.css      # Main CSS import
│   ├── js/
│   └── images/
├── media/
│   ├── avatars/            # User avatars
│   ├── badges/             # Achievement badges
│   ├── CungDuong/          # Trek route media
│   ├── trips/              # Trip media
│   ├── community/          # Community post media
│   └── articles/           # Article thumbnails
├── templates/
│   ├── base.html           # Base template for users
│   ├── admin_base.html     # Base template for admin
│   ├── home.html
│   └── partials/           # Reusable components
└── manage.py
```

## 🔒 Security Notes

⚠️ **IMPORTANT**: Current `settings.py` contains development configuration:

- `DEBUG = True` - **Must be disabled in production**
- `SECRET_KEY` is hardcoded - **Must be changed and use environment variables**
- `ALLOWED_HOSTS = []` - **Must add domain when deploying**

### Production Checklist

```python
# settings.py for production
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Additional security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 🎨 Design System

The project uses **TrekViet Design System** with:
- **CSS Variables** for consistent colors, spacing, shadows
- **BEM Methodology** for naming conventions
- **Component-based** architecture
- **Utility classes** for rapid development

Details: See `migration-report.md`

## 📱 Responsive Design

- Supported breakpoints: 576px, 768px, 992px, 1200px
- Mobile-first approach
- Touch-friendly interface

## 🌐 Localization

- Primary language: **Vietnamese** (`LANGUAGE_CODE = 'vi-vn'`)
- Timezone: **Asia/Ho_Chi_Minh**
- Number format: Dot separator for thousands (100.000)

## 📊 Database Models Summary

| Model | Purpose |
|-------|---------|
| TaiKhoanHoSo | User profiles and personal equipment |
| CungDuongTrek | Trekking routes |
| ChuyenDi | Organized trips |
| CongDongBaiViet | Community posts |
| GameHuyHieu | Achievements and badges |
| BaiHuongDan | Knowledge articles |

## 🔧 Administration

### Admin Panel
- URL: `http://127.0.0.1:8000/admin/`
- Dashboard: `http://127.0.0.1:8000/dashboard/`

### Admin Features
- Route management: `/dashboard/cung-duong/`
- Trip management: `/dashboard/trips/`
- Post management: `/dashboard/posts/`
- Report management: `/dashboard/reports/`
- Article management: `/dashboard/articles/`
- User management: `/dashboard/users/`

## 🚀 Future Development Roadmap

### Phase 1: Core Enhancements (Q1 2026)

#### 1.1 GPS & Location Features
- **GPS Check-in Implementation**
  - Complete the existing `ChuyenDiNhatKyHanhTrinh` model with views/templates
  - Real-time location tracking during trips
  - Route visualization on interactive maps
  - Check-in photos with geotags
  
- **Map Integration**
  - Leaflet.js or Mapbox integration for route display
  - Interactive route planning tool
  - Heatmap of popular routes
  - Offline map download capability

#### 1.2 Mobile Experience
- **Progressive Web App (PWA)**
  - Service worker for offline functionality
  - Install prompt for home screen
  - Push notifications support
  - Offline-first architecture for trip data

- **Mobile-optimized UI**
  - Bottom navigation for mobile
  - Swipe gestures for gallery
  - Touch-optimized chat interface

### Phase 2: Social & Communication (Q2 2026)

#### 2.1 Real-time Features
- **WebSocket Integration**
  - Real-time chat with Django Channels
  - Live trip updates and notifications
  - Online/offline status indicators
  - Typing indicators in chat

#### 2.2 Social Features
- **User Following System**
  - Follow other trekkers
  - Activity feed from followed users
  - Friend recommendation algorithm
  
- **Social Sharing**
  - Share routes/trips to social media
  - Public trip pages with SEO optimization
  - Embeddable trip widgets

### Phase 3: Content & Discovery (Q3 2026)

#### 3.1 Advanced Search & Discovery
- **Smart Search**
  - Elasticsearch integration
  - Full-text search across routes, posts, guides
  - Autocomplete suggestions
  - Search filters and facets

- **Recommendation Engine**
  - Route recommendations based on difficulty level
  - Trip suggestions based on user history
  - Similar routes finder
  - Seasonal recommendations

#### 3.2 Content Enhancement
- **Video Support**
  - Video upload and streaming
  - Video thumbnails generation
  - Video playback optimization
  
- **360° Photo Support**
  - Panoramic photo viewer
  - Virtual route tours

### Phase 4: Platform Expansion (Q4 2026)

#### 4.1 API & Integration
- **REST API Development**
  - Django REST Framework implementation
  - GraphQL endpoint (optional)
  - API documentation with Swagger
  - Rate limiting and authentication

- **Third-party Integrations**
  - Weather API integration for route conditions
  - Booking.com/Agoda for accommodation suggestions
  - Transportation APIs for travel planning

#### 4.2 Monetization Features
- **Premium Membership**
  - Ad-free experience
  - Advanced statistics and analytics
  - Priority support
  - Exclusive content access

- **Marketplace**
  - Gear rental/sales platform
  - Guide booking system
  - Tour package listings

### Phase 5: Analytics & Intelligence (2027)

#### 5.1 Analytics Dashboard
- **User Analytics**
  - Personal hiking statistics
  - Achievement progress tracking
  - Activity heatmaps
  - Comparative analytics

- **Admin Analytics**
  - Platform usage metrics
  - Popular routes and trends
  - User engagement metrics
  - Revenue analytics (if applicable)

#### 5.2 Machine Learning Features
- **Difficulty Prediction**
  - ML model to predict route difficulty based on terrain
  - Personalized difficulty ratings based on user skill level

- **Route Optimization**
  - Suggest optimal routes based on fitness level
  - Time prediction accuracy improvement
  - Weather-based route suggestions

### Phase 6: Community & Safety (Ongoing)

#### 6.1 Safety Features
- **Emergency System**
  - SOS button with location sharing
  - Emergency contact notifications
  - Integration with local rescue services
  - Safety check-in reminders

- **Weather Alerts**
  - Real-time weather warnings
  - Route condition updates from community
  - Seasonal hazard notifications

#### 6.2 Community Building
- **Events & Meetups**
  - Community event calendar
  - Local chapter/club management
  - Virtual meetups support

- **Forum System**
  - Discussion boards by topics
  - Q&A section
  - Expert verification badges

### Technical Debt & Optimization

#### Performance
- [ ] Implement Redis caching for frequently accessed data
- [ ] Database query optimization (select_related, prefetch_related)
- [ ] CDN integration for static/media files
- [ ] Image optimization and lazy loading
- [ ] Database indexing review and optimization

#### Code Quality
- [ ] Unit test coverage (target: 80%+)
- [ ] Integration tests for critical flows
- [ ] Code documentation with Sphinx
- [ ] Type hints with mypy
- [ ] Automated code quality checks (Black, Flake8, isort)

#### DevOps
- [ ] CI/CD pipeline setup (GitHub Actions/GitLab CI)
- [ ] Docker containerization
- [ ] Kubernetes deployment configuration
- [ ] Automated backup system
- [ ] Monitoring and logging (Sentry, ELK stack)

#### Security
- [ ] Security audit and penetration testing
- [ ] HTTPS enforcement
- [ ] Content Security Policy (CSP) headers
- [ ] Rate limiting on sensitive endpoints
- [ ] Regular dependency updates

## 📸 Screenshots

### Homepage
![Homepage](./docs/images/homepage.png)

### Route Detail Page
![Route Detail](./docs/images/route-detail.png)

### Trip Planning
![Trip Planning](./docs/images/trip-planning.png)

### Chat Interface
![Chat](./docs/images/chat-interface.png)

### User Profile
![Profile](./docs/images/user-profile.png)

### Admin Dashboard
![Dashboard](./docs/images/admin-dashboard-full.png)

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed

## 👨‍💻 Development Team

This project was developed by a team of students as a final year project:
- **Developer 1**: Treks, Trips, User Admin modules
- **Developer 2**: Community, Knowledge, Gamification, Articles, Reports modules

## 📝 License

This project is a student academic project. All rights reserved.

## 📞 Contact & Support

For support or feedback, please contact:
- **Email**: [your-email@example.com]
- **GitHub Issues**: [repository-url/issues]
- **Documentation**: [Link to full documentation]

## 🙏 Acknowledgments

- Django community for excellent documentation
- Bootstrap team for the CSS framework
- All open-source contributors whose libraries made this project possible
- Our advisors and mentors for guidance throughout development

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Django Version**: 4.2.23  
**Python**: 3.8+

---

<div align="center">
  <p>Built with ❤️ for the Vietnamese trekking community</p>
  <p>
    <a href="#overview">Overview</a> •
    <a href="#key-features">Features</a> •
    <a href="#installation">Installation</a> •
    <a href="#future-development-roadmap">Roadmap</a> •
    <a href="#contributing">Contributing</a>
  </p>
</div>