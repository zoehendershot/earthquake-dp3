import json
import time
import logging
from decimal import Decimal

import boto3
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = "earthquakes"
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def save_earthquake(feature):
    props = feature.get("properties", {})
    geometry = feature.get("geometry", {})
    coords = geometry.get("coordinates", [None, None, None])

    event_id = feature.get("id")
    magnitude = props.get("mag")
    place = props.get("place", "Unknown location")
    event_time_ms = props.get("time")

    if event_id is None or magnitude is None or event_time_ms is None:
        logger.warning(f"Skipping incomplete feature: {feature}")
        return False

    timestamp = int(event_time_ms / 1000)

    item = {
        "source": "usgs",
        "timestamp": timestamp,
        "event_id": event_id,
        "magnitude": Decimal(str(magnitude)),
        "place": place,
        "longitude": Decimal(str(coords[0])) if coords[0] is not None else None,
        "latitude": Decimal(str(coords[1])) if coords[1] is not None else None,
        "depth_km": Decimal(str(coords[2])) if coords[2] is not None else None,
        "url": props.get("url", ""),
        "source_type": "live_ingestion"
    }

    item = {k: v for k, v in item.items() if v is not None}

    table.put_item(Item=item)
    logger.info(f"Saved earthquake {event_id}: M{magnitude} near {place}")
    return True


def lambda_handler(event, context):
    logger.info("Starting USGS earthquake ingestion")

    try:
        response = requests.get(USGS_URL, timeout=20)
        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])

        saved_count = 0

        for feature in features:
            if save_earthquake(feature):
                saved_count += 1

        logger.info(f"Finished ingestion. Saved {saved_count} earthquakes.")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Saved {saved_count} earthquakes"})
        }

    except Exception as e:
        logger.exception(f"Earthquake ingestion failed: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
