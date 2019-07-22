FROM python:3.7.3-alpine
COPY app /app
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir
WORKDIR /app
CMD ["python", "process_exporter.py"]