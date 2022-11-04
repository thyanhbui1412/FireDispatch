3.1 How to build docker and run docker image
Docker image is a bundle of codes, independencies, runtime, library, app, etc. Build a docker image is basically building a dockerfle. In the dockerfile, we use python as a base image, then we define the directory, 
then we use copy command to copy everything in the source folder (src) to /app. Our source is the python script that loops through each pages and traverse keys and extract values from Socrata data using API. Since we have independencies,
we prepared a requirement.txt file to store independencies and install them with pip install. Lastly, Entry point is to set executables that will always run when the container is initiated. We build the docker image by 
running the docker build command where the Dockerfile is.   

3.2 Backgroung statement:
This project loads and analyzez a dataset with millions of NYC fire alarms between 2012 and 2021. This project is applied with the knowledge of principles of containerization, terminal navigation, 
python scripting, artifact deployment and AWS EC2 provisioning.

3.3 Visualization
First, I was very curious to see which type of alarms with the highest amount. I used tag cloud visualization and it shows Medical emergency accounts for most of the alarms. (Visual01)
Next, I wonder how fast each borough and NYC as a whole respond to alarms. I used Timelion, combined with controls and made a dashboard to have showcase corresponding data. 
Overall, Brooklyn and Manhattan has the fastest response time; Bronx and Queens are the slowest and Staten Islands are quite fluctuating. (Visual02)
Response rate is slightly sensitive to the alarm volume (Visual02).
I also found some interesting trends, alarms volume hits the highest during July-September and hits the lowest during November-February. My speculation is winter and summer has certain impacts of fire alarm incidents. (Visual04)
Lastly, I zoomed in at a Chrismast day, fire alarms is quite low compared to other days but somehow peaked at midnight in Manhattan. (Visual03)     
_________________________________
Notes on my timelion in OpenSearch:
Timeline Expression: 
Visual02:
.es(index=bigdataproject1,timefield=incident_datetime,metric=count:incident_datetime).lines(fill=10).yaxis(yaxis=2, label='Fire Alarm Volume').color(pink),
.es(index=bigdataproject1,timefield=incident_datetime,metric=avg:incident_travel_tm_seconds_qy).lines().title('Average Response Time vs Fire Alarm Volume').yaxis(label='Average Seconds')

Visual03:
.es(index=bigdataproject1,split=incident_borough:5,timefield=incident_datetime,metric=avg:incident_travel_tm_seconds_qy).lines().title('Average Response Time').yaxis(label='Average Seconds')