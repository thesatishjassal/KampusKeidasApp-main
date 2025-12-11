from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

import config

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

client = MongoClient(config.MONGO_URI)
db = client.get_default_database()

users_col = db["users"]
menus_col = db["menus"]
orders_col = db["orders"]
announcements_col = db["announcements"]


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return users_col.find_one({"_id": ObjectId(uid)})

def is_admin():
    user = current_user()
    return bool(user and user.get("role") == "admin")

def login_user(user):
    session["user_id"] = str(user["_id"])
    session["role"] = user.get("role", "customer")

def logout_user():
    session.pop("user_id", None)
    session.pop("role", None)

def seed_admin_user():
    if not users_col.find_one({"role": "admin"}):
        pwd_hash = generate_password_hash("Karday@1")
        users_col.insert_one({
            "email": "gourav131291@gmail.com",
            "passwordHash": pwd_hash,
            "role": "admin",
            "createdAt": datetime.datetime.utcnow()
        })

seed_admin_user()


@app.route("/")
def home():
    active_announcements = list(announcements_col.find({"active": True}).sort("createdAt", -1))
    return render_template("index.html", announcements=active_announcements)


@app.route("/menu")
def menu_page():
    return render_template("menu.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = users_col.find_one({"email": email})
        if not user or not check_password_hash(user["passwordHash"], password):
            flash("Invalid email or password", "error")
            return redirect(url_for("login"))
        login_user(user)
        flash("Logged in successfully", "success")
        return redirect(url_for("home"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not email or not password:
            flash("Email and password are required", "error")
            return redirect(url_for("register"))
        if password != confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for("register"))
        if users_col.find_one({"email": email}):
            flash("Email already registered", "error")
            return redirect(url_for("register"))

        pwd_hash = generate_password_hash(password)
        user = {
            "email": email,
            "passwordHash": pwd_hash,
            "role": "customer",
            "createdAt": datetime.datetime.utcnow()
        }
        res = users_col.insert_one(user)
        user["_id"] = res.inserted_id
        login_user(user)
        flash("Account created!", "success")
        return redirect(url_for("home"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for("home"))


@app.route("/my-orders")
def my_orders():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    orders = list(orders_col.find({"userId": user["_id"]}).sort("createdAt", -1))
    return render_template("orders.html", orders=orders)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = users_col.find_one({"email": email, "role": "admin"})
        if not user or not check_password_hash(user["passwordHash"], password):
            flash("Invalid admin credentials", "error")
            return redirect(url_for("admin_login"))
        login_user(user)
        flash("Admin logged in", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html")


@app.route("/admin")
def admin_dashboard():
    if not is_admin():
        return redirect(url_for("admin_login"))
    order_count = orders_col.count_documents({})
    user_count = users_col.count_documents({})
    menu_days = menus_col.count_documents({})
    return render_template("admin_dashboard.html",
                           order_count=order_count,
                           user_count=user_count,
                           menu_days=menu_days)


@app.route("/admin/menu")
def admin_menu():
    if not is_admin():
        return redirect(url_for("admin_login"))
    menus = list(menus_col.find().sort("date", 1))
    return render_template("admin_menu.html", menus=menus)


@app.route("/admin/orders")
def admin_orders():
    if not is_admin():
        return redirect(url_for("admin_login"))
    orders = list(orders_col.find().sort("createdAt", -1))
    return render_template("admin_orders.html", orders=orders)


@app.route("/admin/announcements", methods=["GET", "POST"])
def admin_announcements():
    if not is_admin():
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        active = bool(request.form.get("active"))
        if title and content:
            announcements_col.insert_one({
                "title": title,
                "content": content,
                "active": active,
                "createdAt": datetime.datetime.utcnow()
            })
            flash("Announcement added", "success")
        return redirect(url_for("admin_announcements"))
    anns = list(announcements_col.find().sort("createdAt", -1))
    return render_template("admin_announcements.html", announcements=anns)


@app.post("/admin/announcements/<ann_id>/toggle")
def toggle_announcement(ann_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    ann = announcements_col.find_one({"_id": ObjectId(ann_id)})
    if ann:
        announcements_col.update_one(
            {"_id": ann["_id"]},
            {"$set": {"active": not ann.get("active", False)}}
        )
    return redirect(url_for("admin_announcements"))


@app.get("/api/menu/week")
def api_menu_week():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())
    end = start + datetime.timedelta(days=6)
    docs = list(menus_col.find({
        "date": {
            "$gte": start.isoformat(),
            "$lte": end.isoformat()
        }
    }).sort("date", 1))

    days = []
    for d in docs:
        days.append({
            "id": str(d["_id"]),
            "date": d["date"],
            "weekday": d.get("weekday"),
            "dishes": d.get("dishes", [])
        })
    return jsonify({"weekStart": start.isoformat(), "weekEnd": end.isoformat(), "days": days})


@app.get("/api/menu/today")
def api_menu_today():
    today = datetime.date.today().isoformat()
    doc = menus_col.find_one({"date": today})
    if not doc:
        return jsonify({"date": today, "weekday": None, "dishes": []})
    return jsonify({
        "id": str(doc["_id"]),
        "date": doc["date"],
        "weekday": doc.get("weekday"),
        "dishes": doc.get("dishes", [])
    })


@app.post("/api/admin/menu")
def api_admin_add_menu_day():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(force=True)
    date = data.get("date")
    weekday = data.get("weekday")
    dishes = data.get("dishes", [])

    if not date:
        return jsonify({"error": "date is required"}), 400

    existing = menus_col.find_one({"date": date})
    doc = {
        "date": date,
        "weekday": weekday,
        "dishes": dishes
    }
    if existing:
        menus_col.update_one({"_id": existing["_id"]}, {"$set": doc})
        _id = existing["_id"]
    else:
        res = menus_col.insert_one(doc)
        _id = res.inserted_id
    return jsonify({"id": str(_id)})


@app.delete("/api/admin/menu/<menu_id>")
def api_admin_delete_menu_day(menu_id):
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401
    menus_col.delete_one({"_id": ObjectId(menu_id)})
    return jsonify({"status": "deleted"})


@app.get("/api/transport-info")
def api_transport_info():
    data = {
        "locations": [
            {
                "title": "Mellunmäki Metro (M2)",
                "description": "Metro line M2 towards Helsinki city centre, approx. 25 minutes."
            },
            {
                "title": "Myllypuro Campus",
                "description": "About 5 km from the restaurant (easy bus or bike connection)."
            }
        ]
    }
    return jsonify(data)


@app.post("/api/orders")
def api_create_order():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(force=True)
    items = data.get("items", [])
    pickup_time = data.get("pickupTime")

    if not items:
        return jsonify({"error": "no items"}), 400

    order = {
        "userId": user["_id"],
        "items": items,
        "status": "pending",
        "pickupTime": pickup_time,
        "createdAt": datetime.datetime.utcnow()
    }
    res = orders_col.insert_one(order)
    return jsonify({"id": str(res.inserted_id)}), 201


@app.get("/api/orders/my")
def api_my_orders():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    orders = list(orders_col.find({"userId": user["_id"]}).sort("createdAt", -1))
    def serialize(order):
        order["id"] = str(order["_id"])
        order["_id"] = None
        order["userId"] = str(order["userId"])
        order["createdAt"] = order["createdAt"].isoformat()
        return order
    return jsonify([serialize(o) for o in orders])


@app.get("/api/admin/orders")
def api_admin_orders():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401
    orders = list(orders_col.find().sort("createdAt", -1))
    out = []
    for o in orders:
        out.append({
            "id": str(o["_id"]),
            "userId": str(o["userId"]),
            "items": o.get("items", []),
            "status": o.get("status"),
            "pickupTime": o.get("pickupTime"),
            "createdAt": o["createdAt"].isoformat()
        })
    return jsonify(out)


@app.patch("/api/admin/orders/<order_id>")
def api_admin_update_order(order_id):
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(force=True)
    status = data.get("status")
    if not status:
        return jsonify({"error": "status required"}), 400
    orders_col.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": status}})
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)