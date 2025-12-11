from pymongo import MongoClient
import datetime
import config

client = MongoClient(config.MONGO_URI)
db = client.get_default_database()
menus_col = db["menus"]

def get_week_dates():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    days = []
    for i in range(5):
        d = monday + datetime.timedelta(days=i)
        days.append(d)
    return days

def main():
    week_days = get_week_dates()
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    sample_menus = [
        [
            {
                "name": "Chicken Pasta",
                "description": "Creamy chicken pasta with parmesan",
                "price": 10.50,
                "diet": ["L"],
                "allergens": ["gluten", "milk"]
            },
            {
                "name": "Veggie Soup",
                "description": "Tomato and lentil soup served with bread",
                "price": 9.00,
                "diet": ["V", "Ve"],
                "allergens": ["gluten"]
            }
        ],
        [
            {
                "name": "Beef Lasagna",
                "description": "Classic lasagna with salad",
                "price": 11.00,
                "diet": ["L"],
                "allergens": ["gluten", "milk"]
            },
            {
                "name": "Vegan Curry",
                "description": "Chickpea and vegetable curry with rice",
                "price": 9.80,
                "diet": ["Ve"],
                "allergens": []
            }
        ],
        [
            {
                "name": "Salmon with Potatoes",
                "description": "Oven baked salmon, dill sauce and potatoes",
                "price": 11.50,
                "diet": ["G", "L"],
                "allergens": ["fish", "milk"]
            },
            {
                "name": "Feta Salad",
                "description": "Green salad with feta cheese and seeds",
                "price": 9.50,
                "diet": ["V", "G"],
                "allergens": ["milk", "sesame"]
            }
        ],
        [
            {
                "name": "Meatballs and Mashed Potatoes",
                "description": "Finnish style meatballs with lingonberry jam",
                "price": 10.90,
                "diet": ["L"],
                "allergens": ["milk", "gluten", "egg"]
            },
            {
                "name": "Veggie Burger",
                "description": "Plant-based burger with fries",
                "price": 10.50,
                "diet": ["Ve"],
                "allergens": ["gluten", "sesame"]
            }
        ],
        [
            {
                "name": "Pizza Buffet",
                "description": "Selection of pizzas, including vegetarian option",
                "price": 11.90,
                "diet": ["L", "V"],
                "allergens": ["gluten", "milk"]
            },
            {
                "name": "Caesar Salad",
                "description": "Chicken Caesar salad with croutons",
                "price": 10.20,
                "diet": ["L"],
                "allergens": ["milk", "gluten", "egg", "fish"]
            }
        ],
    ]

    print("Inserting sample menu for this week...")
    for i, d in enumerate(week_days):
        date_str = d.isoformat()
        weekday = weekday_names[i]

        menus_col.update_one(
            {"date": date_str},
            {
                "$set": {
                    "date": date_str,
                    "weekday": weekday,
                    "dishes": sample_menus[i]
                }
            },
            upsert=True
        )
        print(f"  - {weekday} ({date_str})")

    print("Done! Check your /menu page now.")

if __name__ == "__main__":
    main()