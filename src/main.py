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
    
