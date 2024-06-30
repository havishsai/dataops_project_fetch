# ETL Project for PII Masking

This project implements an ETL (Extract, Transform, Load) pipeline that processes JSON data containing user login behavior from an AWS SQS queue, masks personal identifiable information (PII), and loads the masked data into a PostgreSQL database.

## Project Overview

The main functionality of this ETL application includes:
- Reading JSON formatted messages from an AWS SQS Queue simulated by LocalStack.
- Masking PII data fields (`device_id` and `ip`) using SHA-256 hashing.
- Loading the transformed data into a PostgreSQL database.

## Technologies Used

- Python 3.8+
- PostgreSQL
- Docker and Docker Compose
- AWS SDK for Python (Boto3)
- LocalStack for local AWS simulation
- Psycopg2 - PostgreSQL database adapter for Python

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Docker
- Docker Compose
- Python 3.8 or higher
- pip for Python package management

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/havishsai/dataops_project_fetch.git
   cd dataops_project_fetch
   ```
2. **Run Docker Compose**
   ```bash
   docker-compose up -d
   ```
### Verifing
Now, when the container is up and running successfully, the python ***etl.py*** script will run and execute the corresponding operations. We can verify by querying the postgres database.

we can follow the bellow commands to query the database and verify the successful run of the script:

1. **Connect to the Database**
   ```bash
   psql -d postgres -U postgres -p 5432 -h localhost -W
   ```
2. **Querying the Database**
   ```sql
    select * from user_logins;
   ```

   
## Code Examples and Documentation

### Hashing Function with Documentation String

Below is the Python function used for hashing personal identifiable information (PII). This example includes a detailed docstring explaining the function's purpose, parameters, and return value.

```python
import hashlib

def mask_pii(data, salt="fixed_salt_value"):
    """
    Mask PII data using SHA-256 hash function with a fixed salt for enhanced security.

    Parameters:
    data (dict): A dictionary containing the PII fields 'device_id' and 'ip'.
    salt (str): A fixed salt added to the hash function for additional security.

    Returns:
    dict: A dictionary with masked PII data.
    """
    hasher_device = hashlib.sha256()
    hasher_device.update((salt + data['device_id']).encode())
    masked_device_id = hasher_device.hexdigest()

    hasher_ip = hashlib.sha256()
    hasher_ip.update((salt + data['ip']).encode())
    masked_ip = hasher_ip.hexdigest()

    return {"masked_device_id": masked_device_id, "masked_ip": masked_ip}

  ```


### Processing Messages from SQS and Inserting into PostgreSQL

Below is a detailed Python function used for processing messages from an AWS SQS queue and inserting the transformed data into a PostgreSQL database. The function includes comprehensive docstrings explaining its purpose, parameters, and functionality.

```python
def process_messages():
    """
    Retrieves messages from an AWS SQS queue, processes each message to mask personal identifiable information (PII),
    and inserts the masked data into a PostgreSQL database.

    The function handles message retrieval, data transformation through masking, and database insertion in a seamless manner,
    ensuring that each message is either successfully processed and deleted or an error is logged without crashing the application.

    No parameters are needed as the function assumes access to global variables for SQS client, database connection,
    and queue URL configurations.

    Usage:
    This function should be called within a service that continuously monitors an SQS queue, making sure it handles
    incoming data in real-time. It's ideal for environments where data privacy is paramount and efficient data handling
    is required.

    Error Handling:
    The function includes robust error handling that logs any issues encountered during the message processing steps.
    This ensures that operations can be audited and that the system remains resilient in the face of intermittent failures.
    
    Returns:
    None: This function does not return a value; it processes messages and commits them directly to the database.
    """
    conn = get_conn()  # Retrieve database connection from a connection pool
    cur = conn.cursor()  # Create a cursor object from the connection
    try:
        response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=20)
        messages = response.get('Messages', [])
        for msg in messages:
            data = json.loads(msg['Body'])
            if "device_id" not in data:
                continue  # Skip processing if data does not include 'device_id'
            masked_data = mask_pii(data)  # Mask PII data
            # Flatten and prepare data for insertion
            record = (data['user_id'], data['device_type'], masked_data['masked_ip'],
                      masked_data['masked_device_id'], data['locale'], data['app_version'],
                      datetime.now().date())
            cur.execute("""
                INSERT INTO user_logins (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, record)
            conn.commit()  # Commit the transaction to the database
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg['ReceiptHandle'])  # Delete processed message
    except Exception as e:
        logging.error(f"Error processing message: {e}")  # Log any errors
    finally:
        cur.close()  # Close the cursor
        put_conn(conn)  # Return the connection back to the pool
```

## Next Steps

To enhance the capabilities of this ETL project and address potential scaling, security, and functionality needs, consider the following development paths:

1. **Advanced Masking Techniques**:
   - Explore more sophisticated methods for masking PII that allow for reversibility, such as encryption with secure key management practices.
   - Implement role-based decryption capabilities to ensure that only authorized personnel can access sensitive data in its original form.

2. **Improved Error Handling**:
   - Develop more granular error handling strategies to categorize errors (e.g., recoverable vs. non-recoverable) and implement corresponding recovery mechanisms.
   - Enhance logging to include more context about operations, particularly failures, which can aid in faster troubleshooting and resolution.

3. **Scalability Enhancements**:
   - Introduce horizontal scaling for the application by adding more worker instances that can process messages in parallel, managed by a load balancer or a queue management system.
   - Optimize database interactions by batching inserts or using more efficient data storage formats and technologies.

4. **Performance Monitoring**:
   - Set up a comprehensive monitoring system using tools like Prometheus and Grafana to track the performance and health of both the application and the database.
   - Implement alerts based on thresholds for key performance indicators (KPIs) to proactively manage and mitigate potential issues before they impact the system.

5. **Data Quality Checks**:
   - Integrate automatic data quality checks into the ETL pipeline to verify the integrity and accuracy of the data both pre- and post-transformation.
   - Use these checks to prevent corrupted data from being loaded into the database and to ensure that the system maintains high data quality standards.

## Questions

### How would you deploy this application in production?

To deploy this application in production, we would utilize Docker containers managed by Kubernetes to ensure scalability and resilience. The deployment process would involve setting up a CI/CD pipeline for automated testing and deployment, using tools like Jenkins or GitHub Actions. Additionally, we would integrate monitoring and alert systems using Prometheus and Grafana to maintain optimal performance and reliability.

### What other components would you want to add to make this production ready?

To make this application production-ready, several components would be essential:
- **Security Enhancements**: Implementation of secure access controls, encryption of sensitive data, and regular security audits.
- **Load Balancers**: To distribute incoming traffic and processing loads evenly across multiple instances of the application.
- **Detailed Logging and Monitoring**: Expanded logging for traceability and real-time monitoring tools to detect and respond to operational anomalies.

### How can this application scale with a growing dataset?

Scaling with a growing dataset can be achieved by:
- **Database Optimization**: Implementing sharding or partitioning within the PostgreSQL database to manage larger datasets more efficiently.
- **Increasing Worker Instances**: Scaling out the number of worker instances processing the queue messages to handle increased volume.
- **Utilizing Cloud Auto-scaling Features**: Leveraging cloud provider services to automatically scale resources based on demand.

### How can PII be recovered later on?

Recovering PII, once it has been masked or hashed, is intentionally challenging to enhance security. If reversible masking is necessary, consider using encryption techniques where data can be encrypted and later decrypted using secure keys. Proper key management practices would be essential to ensure data security.

### What are the assumptions you made?

The development of this project is based on several assumptions:
- **Stable and Reliable Infrastructure**: Assumed availability of AWS services and a stable network infrastructure.
- **Consistency in Data Format**: Incoming data in a structured format (JSON) and changes in format are communicated in advance.
- **Scalability of Integrated Services**: Assumed that services like AWS SQS and PostgreSQL can scale according to the demand without significant modifications to the setup.


