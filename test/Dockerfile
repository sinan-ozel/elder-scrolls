FROM python:3.11-slim

WORKDIR /
COPY test/requirements.txt ./
RUN pip install -r requirements.txt
RUN rm requirements.txt

WORKDIR /test
COPY test/*.py ./
COPY test/esp/* ./esp/
RUN echo [Skyrim] > test.ini
RUN echo >> test.ini
RUN echo "Folder = /skyrim/" >> test.ini

CMD ["py.test", "-vv"]
