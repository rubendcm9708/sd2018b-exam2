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
	    return{"Status":"Request failed"}
