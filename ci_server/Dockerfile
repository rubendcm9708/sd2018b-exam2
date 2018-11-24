FROM python:3.6
COPY . /code
WORKDIR /code
RUN pip3.6 install --upgrade pip
RUN pip3.6 install -r requirements.txt
CMD ./app.sh
