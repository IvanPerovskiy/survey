FROM python:3.9
ENV PYTHONUNBUFFERED 1

WORKDIR /app/
COPY . /app/
EXPOSE 8000 8000

RUN pip install -r requirements.txt
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]
