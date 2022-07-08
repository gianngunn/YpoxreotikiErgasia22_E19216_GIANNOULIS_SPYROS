FROM python:3.9.7

ADD ergasiaex.py .

RUN pip install pymongo flask datetime 

EXPOSE 5000

CMD [ "python", "./ergasiaex.py" ]