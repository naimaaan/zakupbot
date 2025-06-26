import requests
import datetime

API_URL = "https://zakup.sk.kz/eprocplan/open-api/plan-extract/filter"
DOWNLOAD_URL_BASE = "https://zakup.sk.kz/eprocplan/api/plan/download/"

def ms_to_date(ms):
    """Преобразует timestamp в читаемую дату"""
    return datetime.datetime.fromtimestamp(ms / 1000).strftime('%Y-%m-%d')

def fetch_procurement_plans(year=2025, max_pages=20):
    all_plans = []

    for page in range(max_pages):
        params = {
            "year": year,
            "size": 20,
            "page": page,
        }

        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()  # ← это сразу список!
        all_plans.extend(data)

    return all_plans


if __name__ == "__main__":
    plans = fetch_procurement_plans()

    for plan in plans:
        date = ms_to_date(plan["approveDate"]) if "approveDate" in plan else "–"
        customer = plan.get("customerName", "–")
        year = plan.get("year", "–")
        plan_type = plan.get("planType", "–")
        file_uid = plan.get("excelFileUid", None)
        excel_url = f"{DOWNLOAD_URL_BASE}{file_uid}" if file_uid else "–"

        print(f"📅 Дата: {date}, 🏢 Заказчик: {customer}, 📘 Год: {year}, 📂 Тип: {plan_type}, 📄 Excel: {excel_url}")
