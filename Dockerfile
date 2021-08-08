# anaconda3 base
# https://hub.docker.com/r/continuumio/anaconda3
FROM continuumio/anaconda3
# need to update apt package repo before we can install packages with apt
# RUN conda install otehr packages (if needed)
RUN conda install -y dash
RUN pip install pyowm
# set the directory in the container we want to work in
WORKDIR /app
# where from on your machine and where to on the container
COPY ./App .

# command to autorun our project conde in the container
CMD ["python", "weather_widget.py"]