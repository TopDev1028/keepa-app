import csv
import requests
from prettytable import PrettyTable
import os
import datetime
from googletrans import Translator
from tabulate import tabulate
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ["KEEPA_API"]
translator = Translator()
current_directory = os.getcwd()

current_date = datetime.date.today()
asin_result_file_name = os.path.join(
    current_directory, "results", "asin", current_date.strftime("%Y-%m-%d") + ".csv"
)


def translate_en_es(strings):
    translated_strings = strings
    translate_ids = [
        1,
        2,
        3,
        4,
        6,
        len(strings) - 10,
        len(strings) - 9,
        len(strings) - 8,
        len(strings) - 7,
        len(strings) - 6,
        len(strings) - 5,
        len(strings) - 4,
        len(strings) - 3,
        len(strings) - 2,
        len(strings) - 1,
    ]
    for id in translate_ids:
        string = strings[id]
        print(string)
        # string = string.strip()
        if string == "" or string == None:
            translated_string = ""
        else:
            translation = translator.translate(string, dest="es", src="auto")

        translated_string = translation.text if translation is not None else ""
        translated_strings[id] = translated_string
        print(translated_string)
    return translated_strings


def scrap():
    asin_scrap()
    filter_scrap()


def asin_scrap():
    ASINS = []
    with open(
        os.path.join(
            current_directory,
            "settings",
            "asins.csv",
        ),
        "r",
    ) as file:
        csv_reader = csv.reader(file)

        for row in csv_reader:
            ASINS.append(row[0])

    params = {
        "key": API_KEY,
        "domain": "1",
        "asin": ",".join(ASINS),
        "stats": 30,
    }

    response = requests.get("https://api.keepa.com/product", params=params)

    print(response.url)

    # CSV header part
    headers = [
        "ASIN",
        "Title",
        "Description",
        "Manufacturer",
        "Brand",
        "Model",
        # "Color",
        "Prime Eligible",
        "Current",
        "Average",
        "30 Day Average",
        "90 Day Average",
        "180 Day Average",
        "365 Day Average",
    ]
    attrs = ["asin", "title", "description", "manufacturer", "brand", "model"]
    for i in range(1, 11):
        headers.append("Feature " + str(i))

    table_data = []
    if response.status_code == 200:
        products_data = response.json()["products"]
        for product in products_data:
            temp = []
            features = [""] * 10

            for attr in attrs:
                temp.append(product[attr])
            for index, value in enumerate(product["features"]):
                features[index] = value
            temp.append(product["stats"]["buyBoxIsPrimeEligible"])

            # Price part
            stats = product["stats"]

            statsKey = ["current", "avg", "avg30", "avg90", "avg180", "avg365"]
            for key in statsKey:
                price = 0
                for item in stats[key]:
                    if item != -1 and item != None:
                        price += item
                print(price)
                temp.append(str(price) + "$")

            temp = temp + features
            translated_temp = translate_en_es(temp)

            table_data.append(translated_temp)
        df = pd.DataFrame(table_data, columns=headers)
        df.to_csv(asin_result_file_name, index=False, encoding="utf-8")
    else:
        print(f"Error: {response.status_code}")


def filter_scrap():
    pass
