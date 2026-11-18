import random
from pathlib import Path

import pandas as pd

rng = random.Random(42)  
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ---------- SUPPLIERS ----------
suppliers = pd.DataFrame([
    ("S01", "Annapurna Agro Traders",   "Indore",     "Madhya Pradesh", 5),
    ("S02", "Gokul Dairy Distributors", "Pune",       "Maharashtra",    2),
    ("S03", "Crunchy Foods Pvt Ltd",    "Ahmedabad",  "Gujarat",        4),
    ("S04", "Fresh Sip Beverages",      "Mumbai",     "Maharashtra",    3),
    ("S05", "Glow Personal Care",       "Gurugram",   "Haryana",        6),
    ("S06", "HomeShine Products",       "Bengaluru",  "Karnataka",      5),
    ("S07", "Tasty Pantry Foods",       "Chennai",    "Tamil Nadu",     7),
    ("S08", "PaperCraft Stationers",    "Sivakasi",   "Tamil Nadu",     8),
    ("S09", "Kisan Wholesale Mart",     "Nagpur",     "Maharashtra",    9),
    ("S10", "Metro Snacks & Foods",     "Delhi",      "Delhi",          4),
], columns=["supplier_id", "supplier_name", "city", "state", "avg_lead_time_days"])

# ---------- STORES ----------
stores = pd.DataFrame([
    ("ST01", "StockWise Pune - Kothrud",       "Pune",      "Maharashtra", "West"),
    ("ST02", "StockWise Mumbai - Andheri",     "Mumbai",    "Maharashtra", "West"),
    ("ST03", "StockWise Delhi - Saket",        "Delhi",     "Delhi",       "North"),
    ("ST04", "StockWise Bengaluru - Indiranagar", "Bengaluru", "Karnataka", "South"),
    ("ST05", "StockWise Hyderabad - Madhapur", "Hyderabad", "Telangana",   "South"),
    ("ST06", "StockWise Chennai - T Nagar",    "Chennai",   "Tamil Nadu",  "South"),
], columns=["store_id", "store_name", "city", "state", "region"])

# ---------- PRODUCTS ----------
# (sku_name, mrp in Rs, gst_rate %, shelf_life_days or None)
catalog = {
    "Staples & Grains": (["S01", "S09"], ["DesiHarvest", "KisanGold", "AnnaPure"], [
        ("Basmati Rice 5 kg", 620, 5, 365), ("Sona Masoori Rice 10 kg", 640, 5, 365),
        ("Whole Wheat Atta 5 kg", 260, 5, 180), ("Toor Dal 1 kg", 180, 5, 365),
        ("Moong Dal 1 kg", 150, 5, 365), ("Chana Dal 1 kg", 110, 5, 365),
        ("Masoor Dal 1 kg", 105, 5, 365), ("Besan 500 g", 85, 5, 180),
        ("Sugar 1 kg", 52, 5, 365), ("Iodised Salt 1 kg", 28, 0, 730),
        ("Poha 500 g", 55, 5, 270), ("Suji Rava 500 g", 48, 5, 270),
        ("Sunflower Oil 1 L", 165, 5, 270), ("Groundnut Oil 1 L", 215, 5, 270),
        ("Turmeric Powder 200 g", 72, 5, 365)]),
    "Dairy": (["S02"], ["GokulFresh", "PureMoo", "DairyDelight"], [
        ("Full Cream Milk 1 L", 68, 0, 4), ("Toned Milk 1 L", 56, 0, 4),
        ("Double Toned Milk 500 ml", 27, 0, 4), ("Curd 400 g", 40, 5, 10),
        ("Curd 1 kg", 90, 5, 10), ("Paneer 200 g", 90, 5, 21),
        ("Butter 100 g", 58, 5, 180), ("Butter 500 g", 275, 5, 180),
        ("Ghee 500 ml", 340, 5, 365), ("Ghee 1 L", 650, 5, 365),
        ("Cheese Slices 200 g", 140, 5, 180), ("Mozzarella Cheese 200 g", 150, 5, 120),
        ("Flavoured Milk 200 ml", 30, 18, 90), ("Sweet Lassi 200 ml", 25, 5, 30),
        ("Buttermilk 200 ml", 15, 5, 15)]),
    "Snacks": (["S03", "S10"], ["CrunchTime", "MunchBox", "SnackBazaar"], [
        ("Salted Chips 50 g", 20, 5, 120), ("Masala Chips 50 g", 20, 5, 120),
        ("Aloo Bhujia 400 g", 110, 5, 150), ("Moong Dal Namkeen 200 g", 60, 5, 150),
        ("Mixture 400 g", 100, 5, 150), ("Cream Biscuits 120 g", 30, 18, 180),
        ("Glucose Biscuits 200 g", 25, 18, 180), ("Marie Biscuits 250 g", 40, 18, 180),
        ("Choco Cookies 150 g", 50, 18, 180), ("Milk Chocolate Bar 40 g", 45, 18, 270),
        ("Chocolate Bar 100 g", 110, 18, 270), ("Instant Noodles Masala 70 g", 14, 5, 270),
        ("Popcorn 60 g", 30, 5, 120), ("Roasted Peanuts 200 g", 55, 5, 150),
        ("Namkeen Sev 200 g", 45, 5, 150)]),
    "Beverages": (["S04"], ["FreshSip", "TropiPure", "ChaiChamp"], [
        ("Mango Drink 600 ml", 45, 18, 180), ("Mango Drink 200 ml", 20, 18, 180),
        ("Packaged Water 1 L", 20, 18, 365), ("Packaged Water 2 L", 35, 18, 365),
        ("Orange Juice 1 L", 120, 5, 180), ("Apple Juice 1 L", 125, 5, 180),
        ("Tea Powder 500 g", 250, 5, 365), ("Tea Powder 250 g", 130, 5, 365),
        ("Instant Coffee 100 g", 290, 18, 540), ("Instant Coffee 50 g", 160, 18, 540),
        ("Green Tea Bags 25 pcs", 130, 5, 540), ("Lemon Drink 600 ml", 40, 18, 180),
        ("Coconut Water 200 ml", 40, 5, 120), ("Malt Health Drink 500 g", 270, 18, 365),
        ("Rose Syrup 750 ml", 140, 18, 365)]),
    "Personal Care": (["S05"], ["GlowUp", "PureSkin", "FreshNaturals"], [
        ("Shampoo 340 ml", 330, 18, None), ("Conditioner 180 ml", 240, 18, None),
        ("Bathing Soap 4 pack", 150, 18, None), ("Body Wash 250 ml", 250, 18, None),
        ("Toothpaste 200 g", 120, 18, None), ("Toothbrush 3 pack", 90, 18, None),
        ("Face Wash 100 ml", 180, 18, None), ("Moisturiser 200 ml", 260, 18, None),
        ("Sunscreen 50 g", 350, 18, None), ("Hair Oil 200 ml", 110, 18, None),
        ("Deodorant 150 ml", 220, 18, None), ("Hand Wash 250 ml", 99, 18, None),
        ("Sanitary Pads 20 pcs", 180, 5, None), ("Razor 5 pack", 90, 18, None),
        ("Talcum Powder 200 g", 130, 18, None)]),
    "Household": (["S06"], ["HomeShine", "CleanKaro", "SparkleCo"], [
        ("Detergent Powder 1 kg", 130, 18, None), ("Liquid Detergent 1 L", 230, 18, None),
        ("Dishwash Liquid 500 ml", 110, 18, None), ("Dishwash Bar 3 pack", 60, 18, None),
        ("Floor Cleaner 1 L", 190, 18, None), ("Toilet Cleaner 500 ml", 105, 18, None),
        ("Glass Cleaner 500 ml", 120, 18, None), ("Phenyl 1 L", 120, 18, None),
        ("Garbage Bags 30 pcs", 100, 18, None), ("Aluminium Foil 9 m", 75, 18, None),
        ("Tissue Rolls 4 pack", 120, 18, None), ("Agarbatti 100 sticks", 60, 5, None),
        ("Matchbox 10 pack", 20, 5, None), ("Mosquito Repellent Refill 45 ml", 80, 18, None),
        ("Scrub Pad 3 pack", 45, 18, None)]),
    "Packaged Foods": (["S07"], ["TastyPantry", "SwadKitchen", "HomeChef"], [
        ("Tomato Ketchup 500 g", 110, 5, 365), ("Mixed Fruit Jam 500 g", 160, 18, 365),
        ("Peanut Butter 340 g", 190, 18, 365), ("Pasta 500 g", 95, 5, 540),
        ("Instant Soup Pack", 30, 18, 365), ("Corn Flakes 475 g", 190, 18, 270),
        ("Oats 1 kg", 190, 5, 365), ("Muesli 500 g", 250, 18, 270),
        ("Mango Pickle 400 g", 120, 5, 365), ("Tomato Puree 200 g", 55, 5, 270),
        ("Ready Mix Idli 500 g", 90, 5, 270), ("Gulab Jamun Mix 175 g", 80, 18, 270),
        ("Honey 500 g", 220, 5, 540), ("Vermicelli 400 g", 50, 5, 365),
        ("Papad 200 g", 60, 5, 270)]),
    "Stationery": (["S08"], ["PaperCraft", "WriteWell", "SchoolMate"], [
        ("Notebook 172 pages", 60, 0, None), ("Notebook 6 pack", 330, 0, None),
        ("Ball Pen Blue 10 pack", 100, 18, None), ("Gel Pen 5 pack", 75, 18, None),
        ("Pencil 10 pack", 50, 18, None), ("Eraser & Sharpener Set", 30, 18, None),
        ("Geometry Box", 130, 18, None), ("A4 Paper 500 sheets", 380, 18, None),
        ("Sticky Notes 100 sheets", 60, 18, None), ("Highlighter 4 pack", 120, 18, None),
        ("Permanent Marker 2 pack", 80, 18, None), ("Glue Stick", 25, 18, None),
        ("Cello Tape", 40, 18, None), ("Stapler", 120, 18, None),
        ("Drawing Book", 70, 0, None)]),
}

rows, n = [], 1
for category, (sup_ids, brands, items) in catalog.items():
    for i, (name, mrp, gst, shelf) in enumerate(items):
        unit_cost = round(mrp / (1 + gst / 100) * rng.uniform(0.72, 0.88), 2)  # 12-28% margin on MRP
        rows.append((f"P{n:03d}", name, category, brands[i % len(brands)],
                     unit_cost, mrp, gst, sup_ids[i % len(sup_ids)], shelf))
        n += 1

products = pd.DataFrame(rows, columns=[
    "product_id", "sku_name", "category", "brand", "unit_cost", "mrp",
    "gst_rate", "supplier_id", "shelf_life_days"])

# ---------- SANITY CHECKS ----------
assert products["product_id"].is_unique, "Duplicate product IDs"
assert (products["unit_cost"] < products["mrp"]).all(), "Cost must be below MRP"
assert products["supplier_id"].isin(suppliers["supplier_id"]).all(), "Unknown supplier"
assert products["gst_rate"].isin([0, 5, 18]).all(), "Unexpected GST slab"
assert (products["unit_cost"] < products["mrp"] / (1 + products["gst_rate"] / 100)).all(), "Cost above ex-GST price"

# ---------- SAVE ----------
suppliers.to_csv(DATA_DIR / "suppliers.csv", index=False)
stores.to_csv(DATA_DIR / "stores.csv", index=False)
products.to_csv(DATA_DIR / "products.csv", index=False)

print(f"suppliers: {len(suppliers)} rows | stores: {len(stores)} rows | products: {len(products)} rows")
print(products.groupby("category").size())
print(products.head())