# anaconda3 base
# https://hub.docker.com/r/continuumio/anaconda3
FROM continuumio/anaconda3
# RUN conda install other packages (if needed)
RUN pip install dash
RUN pip install dash-leaflet
RUN pip install pyowm
# set the directory in the container we want to work in
WORKDIR /app
# where from on your machine and where to on the container
COPY ./App .

# command to autorun our project conde in the container
CMD ["python", "index.py"]