# Restaurant Project - Final Version

Full project according to assignment:

- Flask + MongoDB backend (REST APIs)
- Home page with announcements and open transport info
- Weekly lunch menu from JSON API with today's menu highlighted
- Prices, dietary restrictions, allergens
- Customer registration/login
- Shopping cart and order creation
- My Orders page
- Admin login + dashboard
- Admin: manage orders, menu listing, announcement management
- Seed script to insert weekly menu data

## Setup

1. Go into backend folder:

   ```bash
   cd backend
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables or create `.env`:

   ```env
   MONGO_URI=mongodb://localhost:27017/restaurant_project
   SECRET_KEY=change-me
   ```

4. Ensure MongoDB is running locally.

5. (Optional but recommended) Seed a weekly lunch menu:

   ```bash
   python seed_menu.py
   ```

6. Run the app:

   ```bash
   python app.py
   ```

7. Open in browser:

   - http://127.0.0.1:5000/
   - Admin login: http://127.0.0.1:5000/admin/login  
     - email: admin@example.com  
     - password: admin123