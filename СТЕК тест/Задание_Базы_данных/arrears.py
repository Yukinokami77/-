import psycopg2
from psycopg2.extras import RealDictCursor
from tabulate import tabulate
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import json

def load_db_config(file_path: str):
    try:
        with open(file_path, "r") as config_file:
            return json.load(config_file)
    except Exception as e:
        print(f"Ошибка при загрузке конфигурации базы данных: {e}")
        return None
        os.system("pause")

def абоненты_с_задолженностью(beginning_period: str, number_months: int, db_config: dict):
    beginning_date = datetime.strptime(beginning_period, "%Y-%m-%d")
    end_date = beginning_date + relativedelta(months=number_months - 1)
    end_date = end_date + relativedelta(day=31)  
    
    formatted_beginning_period = beginning_date.strftime("%d.%m.%Y")
    formatted_end_period = end_date.strftime("%d.%m.%Y")
        
    query = f"""
    WITH period AS (
        SELECT generate_series(
            DATE '{beginning_period}', 
            DATE '{beginning_period}' + INTERVAL '{number_months} months', 
            '1 month'
        )::DATE AS month
    ),
    payments_in_period AS (
        SELECT
            COALESCE(f.fio, l.name) AS subscriber,
            date_trunc('month', p.date) AS month,
            p.date AS last_payment_date,
            p.sum AS last_payment_amount,
            p.physical_entity AS physical_entity,
            p.legal_entity AS legal_entity
        FROM payments p
        LEFT JOIN physical_entitys f ON p.physical_entity = f.id
        LEFT JOIN legal_entitys l ON p.legal_entity = l.id
        WHERE p.date BETWEEN DATE '{beginning_period}' AND DATE '{beginning_period}' + INTERVAL '{number_months} months'
    ),
    summary AS (
        SELECT
            subscriber,
            COUNT(DISTINCT month) AS months_paid,
            MAX(last_payment_date) AS last_payment_date
        FROM payments_in_period
        GROUP BY subscriber
    )
    SELECT
        COALESCE(f.fio, l.name) AS subscriber,
        COALESCE(summary.months_paid, 0) AS months_paid,
        summary.last_payment_date,
            (SELECT p.sum
            FROM payments p
            LEFT JOIN physical_entitys f2 ON p.physical_entity = f2.id
            LEFT JOIN legal_entitys l2 ON p.legal_entity = l2.id
            WHERE COALESCE(f2.fio, l2.name) = COALESCE(f.fio, l.name)
                AND p.date <= summary.last_payment_date
            ORDER BY p.date DESC
            LIMIT 1) AS last_payment_amount
    FROM physical_entitys f
    FULL OUTER JOIN legal_entitys l ON FALSE
    LEFT JOIN summary ON summary.subscriber = COALESCE(f.fio, l.name)
    WHERE COALESCE(summary.months_paid, 0) < {number_months};
    """

    try:
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                results = cur.fetchall()

                all_months = [
                    (datetime.strptime(beginning_period, "%Y-%m-%d") + relativedelta(months=i)).date()
                    for i in range(number_months)
                ]
                all_months_str = [month.strftime("%Y-%m") for month in all_months] 

                for row in results:
                    paid_months = set()  
                    if row["months_paid"] > 0:
                        paid_months.add(row["last_payment_date"].strftime("%Y-%m"))  
                    unpaid_months = [month for month in all_months_str if month not in paid_months]
                    row["unpaid_months"] = unpaid_months

                return results, formatted_beginning_period, formatted_end_period
    except Exception as e:
        print(f"Ошибка: {e}")
        os.system("pause")

# Загрузка конфигурации базы данных
db_config = load_db_config("db_config.json")
if not db_config:
    os.system("pause")
    exit("Конфигурационный файл базы данных не найден или содержит ошибки.")
    

print("Введите начальный период (YYYY-MM-DD): ")
beginning_period = str(input())
print("Введите количество месяцев: ")
number_months = int(input())

results, formatted_beginning_period, formatted_end_period = абоненты_с_задолженностью(beginning_period, number_months, db_config)

if results:
    headers = ["Абонент", "Месяцев оплачено", "Дата последнего платежа", "Сумма последнего платежа"]
    rows = [
        [
            row["subscriber"],
            row["months_paid"],
            row["last_payment_date"] if row["last_payment_date"] else "[NULL]",
            row["last_payment_amount"] if row["last_payment_amount"] else "[NULL]"
        ]
        for row in results
    ]
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    print("\nКомментарий:")
    print(f"Период: {formatted_beginning_period} - {formatted_end_period}")
    for row in results:
        if row["months_paid"] == 0:
            print(f"{row['subscriber']}: нет платежей ни в одном месяце периода")
        elif row["unpaid_months"]:
            missing_months = ", ".join(row["unpaid_months"])
            print(f"{row['subscriber']}: нет платежей за {missing_months}")
else:
    print("Нет данных для отображения.")

os.system("pause")
