FROM python:3.10.16
WORKDIR /
COPY . .
RUN pip install -r requirements.txt
RUN apt update && apt install ./linuxqq_3.2.16-32793_amd64.deb
CMD ["python","test.py"]