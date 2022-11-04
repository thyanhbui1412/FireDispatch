# 1 Background statement:
This project streams data directly into OpenSearch cluster provisioned via AWS and analyzez NYC fire alarms between 2012 and 2021. This project is applied with the knowledge of principles of containerization, terminal navigation, python scripting, artifact deployment and AWS EC2 provisioning.

Data size: ~5M rows
![Gauge](https://github.com/thyanhbui1412/FireDispatch/blob/master/assets/Gauge.png)
# 2 File Structure:
```

├── Dockerfile
├── README.txt
├── requirements.txt
└── src
    └── main.py
 ```      

# 3 How to build docker and run docker image
Docker image is a bundle of codes, independencies, runtime, library, app, etc. Build a docker image is basically building a dockerfle. In the dockerfile, we use python as a base image, then we define the directory, 
then we use copy command to copy everything in the source folder (src) to /app. Our source is the python script that loops through each pages and traverse keys and extract values from Socrata data using API. Since we have independencies,
we prepared a requirement.txt file to store independencies and install them with pip install. Lastly, Entry point is to set executables that will always run when the container is initiated. We build the docker image by 
running the docker build command where the Dockerfile is.  

## Containerize DockerImage
```
# We want to go from the base image of python:3.9
FROM python:3.9

# This is the equivalent of “cd /app” from our host machine
WORKDIR /app

# Let’s copy everything into /app
COPY .  /app

# Installs thedependencies. Passes in a text file.
RUN pip install -r requirements.txt

# This will run when we run our docker container
ENTRYPOINT ["python", "src/main.py"]
```

## Adding independencies:
requirements.txt
```
sodapy==2.1.0
requests==2.26.0
```
## Python Scripting: Building workflow
**Connect data source with sodapy module**
```
from sodapy import Socrata
import requests
from requests.auth import HTTPBasicAuth
import json
import argparse
import sys
import os

 
parser = argparse.ArgumentParser(description='Fire Incident Dispatch Data')
parser.add_argument('--page_size', type=int, help='how many rows to get per page', required=True)
parser.add_argument('--num_pages', type=int, help='how many pages to get in total')
args = parser.parse_args(sys.argv[1:])
print(args)


```

**Connect to ElasticSearch with requests**
```

DATASET_ID=os.environ["DATASET_ID"]     
APP_TOKEN=os.environ["APP_TOKEN"]       
ES_HOST=os.environ["ES_HOST"]           
ES_USERNAME=os.environ["ES_USERNAME"]  
ES_PASSWORD=os.environ["ES_PASSWORD"]  
INDEX_NAME=os.environ["INDEX_NAME"]    
if __name__ == '__main__':
    
    try:
        resp = requests.put(f"{ES_HOST}/{INDEX_NAME}", auth=HTTPBasicAuth(ES_USERNAME, ES_PASSWORD),
                json={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 1
                    },
                    "mappings": {
                        "properties": {
                            "starfire_incident_id": {"type": "float"},
                            "incident_datetime": {"type": "date"},
                            "incident_classification_group": {"type": "keyword"},
                            "incident_borough": {"type": "keyword"},
                            "incident_travel_tm_seconds_qy": {"type": "float"},
                            "incident_response_seconds_qy": {"type": "float"},
                        }
                    },
                }
            )
        resp.raise_for_status()
        print(resp.json())
        
    except Exception as e:
        print("Index already exists! Skipping")    

    client = Socrata("data.cityofnewyork.us", APP_TOKEN, timeout=10000)
```

**Extracting data**
```
    for numpage in range(args.num_pages):
        rows = client.get(DATASET_ID, limit=args.page_size, offset=numpage*args.page_size, where = "incident_datetime IS NOT NULL OR starfire_incident_id IS NOT NULL", order = "incident_datetime DESC") #Here I filtered out rows with empty incident_datetime and starfire_incident)id, use OR because I want to take nulls from both out. I know my code won't scalp all history so I only take the most recent incident, a little tweak with ORDER BY DESC
        es_rows=[]
    
        for row in rows:
            try:
                # Convert
                es_row = {}
                es_row["starfire_incident_id"] = float(row["starfire_incident_id"])
                es_row["incident_datetime"] = row["incident_datetime"]
                es_row["incident_classification_group"] = row["incident_classification_group"]
                es_row["incident_borough"] = row["incident_borough"]
                es_row["incident_travel_tm_seconds_qy"] = float(row["incident_travel_tm_seconds_qy"])
                es_row["incident_response_seconds_qy"] = float(row["incident_response_seconds_qy"])

    
            except Exception as e:
                print (f"Error!: {e}, skipping row: {row}")
                continue
            
            es_rows.append(es_row)
        
```
**Bulk API**
```
        bulk_upload_data = ""
        for line in es_rows:
            print(f'Handling row {line["starfire_incident_id"]}')
            action = '{"index": {"_index": "' + INDEX_NAME + '", "_type": "_doc", "_id": "' + str(line["starfire_incident_id"]) + '"}}'
            data = json.dumps(line)
            bulk_upload_data += f"{action}\n"
            bulk_upload_data += f"{data}\n"
    
    
        try:
            resp = requests.post(f"{ES_HOST}/_bulk", data=bulk_upload_data,auth=HTTPBasicAuth(ES_USERNAME, ES_PASSWORD), headers = {"Content-Type": "application/x-ndjson"})
            resp.raise_for_status()
            print ('Done')
                
        except Exception as e:
            print(f"Failed to insert in ES: {e}")
    
```

## FUN PART: Build Docker and run it!
```
docker build -t dockerimage:1.0 .
```
```
docker run \
 -e DATASET_ID="[insert]" \
-e APP_TOKEN="[insert]" \
-e ES_HOST="[insert]" \
-e ES_USERNAME="[insert]" \
-e ES_PASSWORD="[insert]" \
-e INDEX_NAME="[insert]" \
dockerimange --page_size=[insert] --num_pages=[insert] \
```
# 4 Visualization
First, I was very curious to see which type of alarms with the highest amount. I used tag cloud visualization and it shows Medical emergency accounts for most of the alarms. (Visual01)
Next, I wonder how fast each borough and NYC as a whole respond to alarms. I used Timelion, combined with controls and made a dashboard to have showcase corresponding data. 
Overall, Brooklyn and Manhattan has the fastest response time; Bronx and Queens are the slowest and Staten Islands are quite fluctuating. (Visual02)
Response rate is slightly sensitive to the alarm volume (Visual02).
I also found some interesting trends, alarms volume hits the highest during July-September and hits the lowest during November-February. My speculation is winter and summer has certain impacts of fire alarm incidents. (Visual04)
Lastly, I zoomed in at a Chrismast day, fire alarms is quite low compared to other days but somehow peaked at midnight in Manhattan. (Visual03)     
_________________________________

 
**Visual01:**
![Visual01](https://github.com/thyanhbui1412/FireDispatch/blob/master/assets/Visual01.png)

**Visual02:**
![Visual02](https://github.com/thyanhbui1412/FireDispatch/blob/master/assets/Visual02.png)
Timelion functions
`.es(index=bigdataproject1,timefield=incident_datetime,metric=count:incident_datetime).lines(fill=10).yaxis(yaxis=2, label='Fire Alarm Volume').color(pink),
.es(index=bigdataproject1,timefield=incident_datetime,metric=avg:incident_travel_tm_seconds_qy).lines().title('Average Response Time vs Fire Alarm Volume').yaxis(label='Average Seconds')`

**Visual03:**
![Visual03](https://github.com/thyanhbui1412/FireDispatch/blob/master/assets/Visual03.png)
Timelion functions
`.es(index=bigdataproject1,split=incident_borough:5,timefield=incident_datetime,metric=avg:incident_travel_tm_seconds_qy).lines().title('Average Response Time').yaxis(label='Average Seconds')`

**Visual04:**
![Visual04](https://github.com/thyanhbui1412/FireDispatch/blob/master/assets/Visual04.png)
