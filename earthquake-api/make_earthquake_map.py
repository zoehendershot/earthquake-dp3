import boto3
from decimal import Decimal
import matplotlib.pyplot as plt
import geopandas as gpd
import geodatasets

TABLE_NAME = "earthquakes"
BUCKET_NAME = "zoe-earthquake-plots"
PLOT_KEY = "dp3/earthquakes/latest.png"
AWS_REGION = "us-east-1"

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)
s3 = boto3.client("s3", region_name=AWS_REGION)


def to_float(x):
    if isinstance(x, Decimal):
        return float(x)
    return x


items = []
response = table.scan()
items.extend(response.get("Items", []))

while "LastEvaluatedKey" in response:
    response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
    items.extend(response.get("Items", []))

longitudes = []
latitudes = []
magnitudes = []

for item in items:
    if "longitude" in item and "latitude" in item and "magnitude" in item:
        longitudes.append(to_float(item["longitude"]))
        latitudes.append(to_float(item["latitude"]))
        magnitudes.append(to_float(item["magnitude"]))

sizes = [(mag ** 4) * 2 for mag in magnitudes]

world = gpd.read_file(geodatasets.get_path("naturalearth.land"))

fig, ax = plt.subplots(figsize=(15, 8))

world.plot(
    ax=ax,
    color="#f0f0f0",
    edgecolor="white",
    linewidth=0.4
)

ax.scatter(
    longitudes,
    latitudes,
    s=sizes,
    alpha=0.6,
    edgecolors="black",
    linewidths=0.35
)

ax.set_title(
    "Global Earthquake Activity (Magnitude 4.5+) — Last 2 Years",
    fontsize=18,
    pad=18
)

ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_xlim(-180, 180)
ax.set_ylim(-90, 90)
ax.grid(True, linestyle="--", alpha=0.25)

legend_mags = [4.5, 5.5, 6.5, 7.5]
legend_sizes = [(m ** 4) * 2 for m in legend_mags]

handles = [
    plt.scatter([], [], s=size, edgecolors="black", alpha=0.6)
    for size in legend_sizes
]

labels = [f"M {m}" for m in legend_mags]

ax.legend(
    handles,
    labels,
    title="Earthquake Magnitude",
    scatterpoints=1,
    loc="lower left",
    fontsize=10
)

plt.tight_layout()
plt.savefig("latest.png", dpi=200)
plt.close()

s3.upload_file(
    "latest.png",
    BUCKET_NAME,
    PLOT_KEY,
    ExtraArgs={"ContentType": "image/png"}
)

print(f"Uploaded plot to: https://{BUCKET_NAME}.s3.amazonaws.com/{PLOT_KEY}")
