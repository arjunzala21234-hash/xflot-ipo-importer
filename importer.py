
import os
import json
import requests
import firebase_admin

from firebase_admin import credentials, firestore

API_URL = "https://www.xflot.com/api/public/market/ipos"

# Connect to Firebase using GitHub Secret
service_account_json = os.environ["FIREBASE_SERVICE_ACCOUNT"]
service_account_info = json.loads(service_account_json)

cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred)

db = firestore.client()


def text_value(value, fallback="Not available"):
    if value is None or value == "":
        return fallback
    return str(value)


def import_ipos():

    print("Fetching IPO data from Xflot...")

    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()

    result = response.json()

    if result.get("ok") is not True:
        raise Exception("Xflot API did not return success")

    ipos = result.get("ipos", [])

    print("Total IPOs received:", len(ipos))

    batch = db.batch()
    saved = 0

    for ipo in ipos:

        slug = ipo.get("slug")

        if not slug:
            print("Skipping IPO without slug")
            continue

        price_min = ipo.get("priceMin")
        price_max = ipo.get("priceMax")

        if price_min is not None and price_max is not None:
            price = f"₹{price_min} - ₹{price_max}"
        else:
            price = "Not available"

        open_date = text_value(ipo.get("openDate"), "Not announced")
        close_date = text_value(ipo.get("closeDate"), "Not announced")

        data = {
            "slug": slug,
            "name": text_value(ipo.get("name")),
            "category": text_value(ipo.get("board")),
            "status": text_value(ipo.get("status")),
            "dates": f"Open: {open_date} | Close: {close_date}",
            "price": price,
            "lot": text_value(ipo.get("lotSize")),
            "gmp": text_value(ipo.get("lastGmp")),
            "allotment": "Not announced",
            "listing": "Not announced",
            "lastGmpPct": ipo.get("lastGmpPct"),
            "lastSubX": ipo.get("lastSubX"),
            "source": "Xflot",
            "disclaimer": result.get("disclaimer", "")
        }

        document_ref = db.collection("ipos_test").document(slug)
        batch.set(document_ref, data, merge=True)

        saved += 1

    if saved:
        batch.commit()

    print("IPO documents saved:", saved)


if __name__ == "__main__":
    import_ipos()
