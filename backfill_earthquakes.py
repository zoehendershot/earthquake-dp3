import time
import logging
from decimal import Decimal
from datetime import datetime, timedelta, timezone

import boto3
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TABLE_NAME = "earthquakes"
AWS_REGION = "us-east-1"

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
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
        "source_type": "historical_backfill"
    }

    item = {k: v for k, v in item.items() if v is not None}

    table.put_item(Item=item)
    logger.info(f"Saved M{magnitude} near {place}")
    return True


def fetch_month(start_date, end_date):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    params = {
        "format": "geojson",
        "starttime": start_date.strftime("%Y-%m-%d"),
        "endtime": end_date.strftime("%Y-%m-%d"),
        "minmagnitude": 4.5,
        "orderby": "time"
    }

    logger.info(f"Fetching {params['starttime']} to {params['endtime']}")

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    return response.json().get("features", [])


def main():
    logger.info("Starting USGS historical backfill")

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365 * 2)

    current = start
    total_saved = 0

    while current < end:
        next_month = min(current + timedelta(days=30), end)

        try:
            features = fetch_month(current, next_month)

            for feature in features:
                if save_earthquake(feature):
                    total_saved += 1

        except Exception as e:
            logger.exception(f"Failed month starting {current}: {e}")

        current = next_month
        time.sleep(1)

    logger.info(f"Finished backfill. Saved/updated {total_saved} records.")


if __name__ == "__main__":
    main()
