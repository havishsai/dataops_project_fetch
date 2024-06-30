import boto3
import psycopg2
import psycopg2.pool
import hashlib
import json
import logging
from datetime import datetime
from botocore.exceptions import ClientError
from time import sleep

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# AWS SQS setup
sqs = boto3.client('sqs', endpoint_url="http://localstack:4566", region_name="us-east-1", 
                   aws_access_key_id="test", aws_secret_access_key="test")
queue_url = "http://localstack:4566/000000000000/login-queue"

# PostgreSQL connection pool setup
def create_connection_pool():
    retries = 5
    while retries > 0:
        try:
            return psycopg2.pool.SimpleConnectionPool(1, 10, 
                                                      host="postgres",
                                                      port="5432",
                                                      database="postgres",
                                                      user="postgres",
                                                      password="postgres")
        except psycopg2.OperationalError as e:
            logging.warning(f"Failed to connect to database. Retries left: {retries-1}")
            retries -= 1
            sleep(5)  # wait for 5 seconds before trying again
    raise Exception("Failed to connect to the database after several attempts")

conn_pool = create_connection_pool()

def get_conn():
    return conn_pool.getconn()

def put_conn(conn):
    conn_pool.putconn(conn)

def mask_pii(data):
    """ Mask PII data using SHA-256 hash function """
    hasher = hashlib.sha256()
    hasher.update(data['device_id'].encode())
    masked_device_id = hasher.hexdigest()
    hasher.update(data['ip'].encode())
    masked_ip = hasher.hexdigest()
    return {"masked_device_id": masked_device_id, "masked_ip": masked_ip}

def process_messages():
    """ Process messages from SQS queue """
    conn = get_conn()
    cur = conn.cursor()
    try:
        response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=20)
        messages = response.get('Messages', [])
        for msg in messages:
            data = json.loads(msg['Body'])
            if "device_id" not in data:
                continue
            masked_data = mask_pii(data)
            # Flatten and prepare data for insertion
            record = (data['user_id'], data['device_type'], masked_data['masked_ip'],
                      masked_data['masked_device_id'], data['locale'], data['app_version'],
                      datetime.now().date())
            cur.execute("""
                INSERT INTO user_logins (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, record)
            conn.commit()
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg['ReceiptHandle'])
    except Exception as e:
        logging.error(f"Error processing message: {e}")
    finally:
        cur.close()
        put_conn(conn)

if __name__ == "__main__":
    while True:
        process_messages()
