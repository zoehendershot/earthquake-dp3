from chalice import Chalice
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import tempfile
import os
import logging
from datetime import datetime

app = Chalice(app_name="earthquake-api")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = "earthquakes"
BUCKET_NAME = "zoe-earthquake-plots"
PLOT_KEY = "dp3/earthquakes/latest.png"

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
s3 = boto3.client("s3")


def to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


@app.route("/")
def index():
    return {
        "about": "Tracks recent and historical earthquakes using the USGS Earthquake API, storing magnitude, location, depth, and time in DynamoDB.",
        "resources": ["current", "trend", "plot"]
    }


@app.route("/current")
def current():
    try:
        response = table.query(
            KeyConditionExpression=Key("source").eq("usgs"),
            ScanIndexForward=False,
            Limit=1
        )

        items = response.get("Items", [])

        if not items:
            return {"response": "No earthquake data has been collected yet."}

        item = items[0]
        mag = to_float(item["magnitude"])
        place = item.get("place", "unknown location")
        timestamp = int(item["timestamp"])
        dt = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M UTC")

        return {
            "response": f"Latest stored earthquake: magnitude {mag} near {place} at {dt}."
        }

    except Exception as e:
        logger.exception(f"Error in /current: {e}")
        return {"response": "Error retrieving current earthquake data."}


@app.route("/trend")
def trend():
    try:
        response = table.query(
            KeyConditionExpression=Key("source").eq("usgs"),
            ScanIndexForward=False,
            Limit=100
        )

        items = response.get("Items", [])

        if len(items) < 2:
            return {"response": "Not enough earthquake data collected yet to calculate a trend."}

        magnitudes = [float(item["magnitude"]) for item in items]
        avg_mag = sum(magnitudes) / len(magnitudes)
        max_mag = max(magnitudes)

        strongest = max(items, key=lambda x: float(x["magnitude"]))
        place = strongest.get("place", "unknown location")

        return {
            "response": f"Across the latest {len(items)} stored earthquakes, the average magnitude is {round(avg_mag, 2)}. The strongest was magnitude {round(max_mag, 2)} near {place}."
        }

    except Exception as e:
        logger.exception(f"Error in /trend: {e}")
        return {"response": "Error calculating earthquake trend."}


@app.route("/plot")
def plot():
    url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{PLOT_KEY}"
    return {"response": url}

