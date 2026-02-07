# 🏔️ TrekViet - Trekking Route & Expedition Management Platform

**TrekViet** is a professional full-stack platform designed for the trekking and hiking community in Vietnam. It enables users to discover new trails, organize group expeditions with detailed logistics, and share survival expertise.

---

## 🌟 Main Features

### 1. Interactive Home Page
A modern landing page designed to showcase the beauty of Vietnam's nature and provide quick access to popular trails.
> ![Home Page 1](picture/so1.png)
> ![Home Page 2](picture/so2.png)
> ![Home Page 3](picture/so3.png)
> ![Home Page 2](picture/so4.png)
> ![Home Page 3](picture/so5.png)

### 2. Advanced Trek Discovery
A comprehensive library of trekking routes with GIS data.
*   **Technical Specs:** Elevation profiles, total distance, and difficulty levels (Easy to Expert).
*   **Interactive Maps:** Visualized trail paths using GeoJSON.
*   **Suggested Gear:** Automatic equipment checklists tailored to specific terrains.
> ![Trek Discovery](picture/so6.png)
> ![Trek Discovery](picture/so6.1.png)
> ![Trek Discovery](picture/so6.2.png)
### 3. Expedition & Trip Hub
Organize group adventures or join existing expeditions.
*   **Member Management:** Role-based access (Lead, Co-lead, Member) with an approval system for new joiners.
*   **Privacy Controls:** Private trips accessible only via **Secret Invitation Codes**.
*   **Itinerary Planning:** Dynamic timelines to manage day-by-day activities.
> ![Trip Hub](picture/so7.png)
> ![Trip Hub](picture/so7.1.png)


### 4. Real-time Communication Center
Dedicated chat rooms for every trip to ensure seamless coordination.
*   **Rich Messaging:** Supports media sharing, message replies, and reactions.
*   **Notifications:** Instant system alerts for itinerary updates or member requests.
> ![Chat Hub](picture/so8.png)

### 5. Personal Gear & Achievement Dashboard
*   **Inventory Manager:** Track personal trekking equipment and gear conditions.
*   **Activity Stats:** Data-driven tracking of total kilometers conquered and summits reached.
> ![User Dashboard](picture/so9.png)

### 6. Community & Knowledge Base
A social space for sharing experiences and learning survival skills.
*   **Trip Reviews:** Rate and review completed trails with photos.
*   **Survival Guides:** Professional articles on first aid, navigation, and gear prep.
> ![Community Feed](picture/so10.png)
> ![Community Feed](picture/so11.png)
> ![Community Feed](picture/so12.png)
> ![Community Feed](picture/so13.png)

---

## 👑 Administrative Hub (System Command Center)

TrekViet features a high-performance administration dashboard for system owners to monitor, moderate, and educate the community.

### 1. Operations Dashboard
A bird's-eye view of the system's health and real-time activity.
*   **Real-time Metrics:** Monitor "New Members," "Pending Approvals," and "Upcoming Departures."
*   **Risk Management:** Integrated "Risk Warning" system to track potential issues in active trips.
> ![Admin Dashboard](picture/so16.png)
> ![Admin Dashboard](picture/so16.1.png)

### 2. Knowledge Base & Content Management (CMS)
A specialized module for managing professional hiking expertise and survival guides.
*   **Article Management:** Admin-only interface to create, edit, and publish verified survival articles.
*   **Categorization:** Organize knowledge into structured sections like "Survival Skills," "First Aid," and "Gear Guides."
*   **Expert Verification:** Moderating and approving high-quality articles submitted by the community.
> ![Knowledge Management](picture/so21.png)

### 3. Trail & Expedition Moderation
*   **Route Verification:** Admins review user-submitted trails for technical accuracy before they go public.
*   **Trip Oversight:** Power to monitor and manage all active group expeditions for safety compliance.
> ![Content Moderation](picture/so17.png)
> ![Content Moderation](picture/so17.1.png)
> ![Content Moderation](picture/so17.2.png)



### 4. User Safety & Security
*   **Report Handling:** Efficiently process user reports regarding harassment or inappropriate behavior.
*   **Account Control:** Tools to verify professional guides, warn users, or suspend accounts.
*   **Global Broadcasts:** Centralized engine to send urgent weather alerts or system updates to all users.
> ![Security Management](picture/so19.png)
> ![Security Management](picture/so19.1.png)

---
## 🛠️ Technology Stack & Architecture

### **System Architecture**
The project follows the **Django MVT (Model-View-Template)** architecture, modularized into key applications:
- **`treks`**: GIS route data, mapping, and trail review engine.
- **`trips`**: Logistics, member approval logic, and real-time chat infrastructure.
- **`accounts`**: User profiles, gear inventory, and achievement tracking.
- **`community`**: Social feed, discussion logic, and user interactions.
- **`articles`**: CMS for educational content and survival guides.

### **Tech Specs**
- **Backend:** Python 3.8+, Django 4.2
- **Database:** MySQL (Relational data management)
- **Geospatial:** GDAL & GeoJSON for trail mapping.
- **Frontend:** Bootstrap 5, Vanilla JavaScript, AJAX (Chat updates).

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.8+
- MySQL Server
- GDAL Library (required for Map data processing)

### 2. Run the Project
```bash
# Clone the repository
git clone https://github.com/yourusername/trekviet.git
cd trekking-web-trangchu_v3

# Setup virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Database Setup
# 1. Create a MySQL database named 'trekking_db'
# 2. Update settings.py with your DB credentials

# Initialize Database
python manage.py migrate
python manage.py createsuperuser # Create your Admin account

# Start the server
python manage.py runserver