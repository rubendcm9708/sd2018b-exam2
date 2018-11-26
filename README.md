# Exam 2  
**ICESI University**  
**Student name:**  Ruben Dario Ceballos  
**Student ID:** A00054636  
**Email:** rubendcm9708@gmail.com  
**Repository:** https://github.com/rubendcm9708/sd2018b-exam1/tree/rceballos/sd2018b-exam2   
**Subject:** Distributed systems   
**Professor:** Daniel Barragán C.  
**Topic:** Continuous Delivery Infrastructure   

### Objectives  
* Develop artifact automatic building for Continous Delivery  
* Use libraries of programming languages to perform specific tasks  
* Diagnose and execute the needed actions to achieve a stable infrastructure  

### Implemented Technologies  
* Docker  
* CentOS7 (Operative System Box)  
* Github Repository  
* Python3  
* Python3 libraries: Flask, Connexion, Fabric, Requests  
* Ngrok  

### Infrastructure Description  
For this project, we are going to deploy an infrastructure that will allow developers to build and deliver artifacts (Docker images) to a Registry (Docker Images Repository) when a pull request on a Develop branch is merged. Later, these images could be pulled by clients. This infrastructure have three Docker containers that are going to be explained below.  

**Registry:**  
* This CT (Container) works as a local private repository of Docker Images. Here is where the **ci server** is going to push the artifacts, that later can be pulled by clients.  

**CI Server:**  
* This CT have a *Flask* application with an Endpoint service designed with RESTful architecture. This endpoint works as follow:  
  * When a Pull request with the fonts for a new Docker Image is merged to the develop branch , a Webhook attached to the Github repository will trigger the endpoint with a POST request.  
  * The request contains all the information about the Pull request, that helps the endpoint to retrieve the fonts to build the artifact.  
  * The endpoint will build the artifact, and through a docker client session will push the Docker Image to the **registry**.  
 
 **Ngrok:**  
 * This CT creates a tunnel between the **CI server** and the Webhook in Github. Provices a temporary public domain that the webhook can use.  
 
 In the **Figure 1**, we can appreciate the infrastructure used in this project.  
  
![][1]  
**Figure 1:** Deployment Diagram  

### Containers Provisioning ###  

To provision and deploy the containers I'm using Docker compose. The docker-compose.yml have three services, one for each container.  

For the **ngrok**, there is an image *wenight/ngrok* that have all the dependencies to run the services, it just needs a port in the local machine to run, and the domain name and port of the service that is going to be exposed.  
```
  ngrok:
    image: wernight/ngrok
    ports:
      - 0.0.0.0:4040:4040
    links:
      - ci_server
    environment:
      NGROK_PORT: ci_server:8088
```
In the registry, there is image *registry:2* with the libraries and dependencies to create and expose a local repositories of docker images. To guarantee secure access, it needs a domain certificate and key that were created using openssl.
```
  registry:
    image: registry:2
    ports:
      - 5000:5000
    environment:
      REGISTRY_HTTP_ADDR: 0.0.0.0:5000
      REGISTRY_HTTP_TLS_CERTIFICATE: ./certs/domain.crt
      REGISTRY_HTTP_TLS_KEY: ./certs/domain.key
    volumes:
      - ./registry/certs/:/certs
```

This is the **ci_server**, the build process use the Dockerfile in the ci_service directory, that install all the python and pip libraries, and finally deploy the web service with the endpoint running on port 8088. Also, it has a volume related to the local machine's docker socket to run all the docker commands in order to build and push an image.

```
  ci_server:
    build: ci_server
    ports:
     - "8088:8088"
    volumes:
     - //var/run/docker.sock:/var/run/docker.sock
```
The Dockerfile, it uses a centOS7 image with python 3.6. First, it install all the libraries and dependencies. Then, it copies the directory ci_server that contains gm_analytics with the flask application, next it set the enviroment variables to finally run the service.

```
FROM centos/python-36-centos7
COPY . /code
WORKDIR /code
RUN pip3.6 install --upgrade pip
RUN pip3.6 install -r requirements.txt
CMD ./app.sh
```
The app.py set all the enviroment variables, such as LANG (usually the enviroment don't have a selected language), pythonpath to find the archives that are going to be used and the flask enviroment. Finally, it deploy the web service using connexion.  
```
export LANG=en_US.utf8
export PYTHONPATH=$PYTHONPATH:`pwd`
export FLASK_ENV=development
connexion run /code/gm_analytics/swagger/indexer.yaml --debug -p 8088
```
This is the handlers.py, that is used when request to the **ci_server** is made. It first check if the request is a pull request that has been merged by getting the request data, that usually is a JSON file with the PR information. Then, it gets all the fonts to build de docker image, such as the Dockerfile and spec.json with the service name and version. Finally, it builds the image and push it to the **registry**.  
```
import logging
import requests
import json
import docker
from flask import request

def buildimage():
    #Post recieved
    logging.info("Service has been requested")

    #Get post request body and convert to String
    post_body = request.get_data()
    body_toString = str(post_body, 'utf-8')

    #load Json file with body and get merged field with true or false
    json_file = json.loads(body_toString)
    merged=json_file["pull_request"]["merged"]

    #If PR has been merged
    if merged:
        #Get PR id
        pr_id = json_file["pull_request"]["head"]["sha"]

        #Get spec.json
        spec_Url="https://raw.githubusercontent.com/rubendcm9708/sd2018b-exam2/"+pr_id+"/spec.json"
        spec_data=requests.get(spec_Url)
        service_specs=json.loads(spec_data.content)

        #Get Dockerfile content and create Dockerfile
        dockerfile_url="https://raw.githubusercontent.com/rubendcm9708/sd2018b-exam2/"+pr_id+"/Dockerfile"
        dockerfile_data=requests.get(dockerfile_url)
        file = open("/code/gm_analytics/Dockerfile","w")
        file.write(str(dockerfile_data.content, 'utf-8'))
        file.close()

        #Create tag for registry
        tag="192.168.130.122:5000/"+service_specs["service"]["name"]+":"+service_specs["service"]["version"]

        #Create docker client, and build and push image
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        client.images.build(path="/code/gm_analytics/", tag=tag)
        client.images.push(tag)
        client.images.remove(image=tag, force=True)
        return{"Status":"Requested and succesfully"}
    else:
        return{"Status":"Invalid request"}
```
### Deployment ### 
To deploy the containers that have been defined in the docker-compose.yml, run this command:  

```
docker-compose up 
```
After finishing, all the services should be up. To check if everything is running, we can run this command:  
```  
docker-compose ps
```  
We should get a list with all the containers with its states  
![][2]  

Now that we now that everything is up, we need to create a webhook in our repository, this will trigger everytime a pull request is merged and request a POST to the **ci_server**.  To create the webhook, go to settings, webhook and add a new webhook. Github request for a Payload URL, and that's why we need a ngrok running locally. To know what is the URL, we can access to *http://YOUR-IP:4040/status* that is the web server associated to the **ngrok** service, and check the public domain name that has been assigned to our container. In the next image we can see the UI.
![][3]  
Now, add your endpoint path to the public domain name and that is your Payload URL. Select JSON as content type, and select *Let me select individual events*, then check Pull Requests. It should look like this.
![][4]  

Now that everything is running, we need two branches to test the artifact building and delivery. The first one is a *develop* branch, where the pull request is going to be merged, and the second one is the origin branch that have all the fonts that are going to be merged to the *develop* branch. The service that I'm testing, is a simple apache service, so my branch is called *develop-apache* and have this files.

Dockerfile  
```
FROM ubuntu
#Update and install apache2
RUN apt-get update -y
RUN apt-get install apache2 -y
EXPOSE 80
#Run apache2 and show logs 
CMD service apache2 start && tail -f /var/log/apache2/access.log
```
And the spec.json  
```
{
  "service":{
    "name": "apache",
    "version": "0.4.0"
  }
}
```
So, I added, commited and pushed the fonts to *develop-apache*, then I started and merged a Pull Request to *develop*  
![][5]  
And the webhook shows that it did a request with a 200 response from the **ci_server**  
![][6]  
To check if the image has been builded and pushed to the registry, we need to pull the image with its name and version to your ip, and the port of the container. For example, I used this command:  
```
docker pull 192.168.130.122:5000/apache:0.4.0
```
After finishing, we can run the next command to list all the docker images that are in our machine:  
```
docker images
```
The output of this command, should have an image that corresponds with the fonts that were in our origin branch. In my case was this:  
![][7]  

### Problems and Issues ###  
The first problem that I faced, was that my **ci_server** was exiting with a code error because that a containter language had not been selected, so I setted LANG as an UTF 8 for United State english. And finally, I couldn't create a Dockerfile in the **ci_server** to build the image using the fonts in the origin branch, so I mapped the docker.sock of my local machine to the container. 

### Referencias
* https://hub.docker.com/_/registry/
* https://hub.docker.com/_/docker/
* https://docker-py.readthedocs.io/en/stable/index.html
* https://developer.github.com/v3/guides/building-a-ci-server/
* http://flask.pocoo.org/
* https://connexion.readthedocs.io/en/latest/

[1]: images/01_diagrama_delivery.png
[2]: images/docker_ps.png
[3]: images/ngrok.png
[4]: images/webhook.png
[5]: images/merged.png
[6]: images/webhook_request.png
[7]: images/docker_image.png  
