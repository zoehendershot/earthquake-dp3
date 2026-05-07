# USGS Earthquake Tracker

## Overview

This project tracks recent and historical earthquake activity using the United States Geological Survey (USGS) Earthquake API. I chose this data source because earthquake activity changes continuously over time and provides meaningful geospatial and time-series data. 

The system collects earthquake magnitude, location, coordinates, depth, and timestamp information and stores it in a DynamoDB table. The API then provides resources for retrieving the latest earthquake information, summarizing recent trends, and viewing a visualization of global earthquake activity.

## Data Source

Source: USGS Earthquake API

Real-time feed used for ingestion:

https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson

Historical backfill endpoint used:

https://earthquake.usgs.gov/fdsnws/event/1/query

The project tracks earthquakes with magnitude 4.5+ from around the world.

## Ingestion Pipeline

The ingestion pipeline uses a Lambda function triggered by EventBridge once per hour.

Each scheduled run:
1. Pulls the latest earthquake GeoJSON feed from USGS
2. Extracts earthquake magnitude, location, coordinates, depth, and timestamps
3. Stores the data in DynamoDB

A one-time historical backfill script was also used to populate older earthquake records so the API could immediately support trend analysis and visualization.

## Storage Schema

DynamoDB table name:

`earthquakes`

Partition key:

`source` (String)

Sort key:

`timestamp` (Number)

Each item stores:

- `event_id`
- `magnitude`
- `place`
- `longitude`
- `latitude`
- `depth_km`
- `timestamp`
- `url`
- `source_type`

Example item:

```json
{
  "source": "usgs",
  "timestamp": 1778101258,
  "event_id": "us7000abcd",
  "magnitude": 5.3,
  "place": "120 km SE of Tokyo, Japan",
  "longitude": 141.2,
  "latitude": 35.1,
  "depth_km": 22.4
}

```

## API Resources

Base API URL:

`https://umk87rmx76.execute-api.us-east-1.amazonaws.com/api`

---

### `/`

Returns general information about the project, including a short description of the API and the available resources.

---

### `/current`

Returns information about the latest earthquake activity sample from the USGS past-hour earthquake feed. The response includes the number of detected earthquakes and the strongest recent earthquake event.

---

### `/trend`

Returns a summary of recent earthquake trends using stored historical hourly samples. The response includes the average hourly earthquake count and the strongest earthquake recorded in the recent sampling window.
  
---

### `/plot`

Returns a public S3 URL to a PNG visualization of global earthquake activity.

The visualization displays:
- earthquake locations around the world
- bubble size scaled by earthquake magnitude
- historical earthquake activity from the last 2 years
