FROM python:3.8-slim 

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN ["python", "scripts/normalize.py"]

RUN ["python", "scripts/validate.py", ">", "test_results.txt"]

RUN ["python", "build-html.py"]

WORKDIR /usr/src/app/docs

CMD ["python", "-m", "http.server"]