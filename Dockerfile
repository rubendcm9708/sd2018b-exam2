FROM ubuntu

#Update and install apache2
RUN apt-get update -y
RUN apt-get install apache2 -y
EXPOSE 80

#Run apache2 and show logs 
CMD service apache2 start && tail -f /var/log/apache2/access.log
