# Cloud-Based IoT Air Quality Data Analytics System (AWS)

## Project Overview

This project implements a **cloud-based distributed system** for collecting, processing, and distributing
real-time air quality data using **Amazon Web Services (AWS)**.

The system ingests environmental sensor data (PM2.5 and PM10), computes the **Air Quality Index (AQI)**,
stores processed data in a scalable NoSQL database, and exposes results to users through a web-based
application. The architecture is designed to be **scalable, fault-tolerant, and cost-efficient** under
heavy load conditions.

This project was developed as part of a **Cloud Computing academic module** and focuses on real-world
engineering challenges such as **system scalability, performance optimization, cost control, and security**.

---

## System Architecture

The system is composed of the following components:

* **Client Web Application (Flask)**
* **Master Node** for data ingestion and orchestration
* **Worker Nodes** for distributed processing
* **Amazon DynamoDB** for persistent storage
* **Amazon SQS** for request queuing and load management
* **Amazon EC2** for compute resources
* **AWS CloudWatch** for monitoring and observability

The system supports:
* Direct synchronous processing under low load
* Asynchronous queue-based processing under heavy load

---


## Repository Structure

```bash
Cloud-IoT-Air-Quality-Analytics
│
├── app
│   ├── client
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   ├── Procfile
│   │   ├── static
│   │   │   ├── css
│   │   │   └── js
│   │   └── templates
│   │       └── request.html
│   │
│   ├── master
│   │   └── master.py
│   │
│   └── worker
│       └── worker.py
│
├── infrastructure
│   ├── sqs
│   ├── dynamodb
│   └── ec2
│
├── tests
│   └── test_performance.py
│
├── notebooks
│   └── CC_Initialisation.ipynb
│
├── docs
│   ├── Report.pdf
│   └── Instructions.pdf
│
├── images
│   └── figures_from_report.png
│
├── README.md
└── .gitignore
```
---


## Technologies Used

* Python
* Flask
* Amazon EC2
* Amazon DynamoDB
* Amazon SQS
* AWS CloudWatch
* Jupyter Notebook
* REST APIs
* Concurrent programming (ThreadPoolExecutor)

---

## How the System Works

1. Environmental sensor data is fetched from an external API.
2. The Master node computes AQI values and stores results in DynamoDB.
3. Users submit queries via the Flask web application.
4. Under low load, queries are processed immediately.
5. Under heavy load, queries are queued using Amazon SQS.
6. Worker nodes process queued requests asynchronously.
7. Results are returned to users as downloadable CSV files.

---

## Running the Project Locally

To run the project locally:

1. Install the required Python dependencies listed in:
   app/requirements.txt

2. Start the Flask application by executing App.py
   from the app directory.

The web application will be available on the configured port.

---

## Data Ingestion

The master node is responsible for:

* Fetching sensor data
* Calculating AQI values
* Cleaning and structuring data
* Storing results in DynamoDB

This process can be scheduled to run periodically
(e.g. daily updates).

---

## Performance Testing

The performance testing script simulates concurrent users and
high request volumes.

It measures:
* Response time
* Error rate
* System stability under load

This validates system scalability and robustness.

---

## Infrastructure Automation

The notebook located in:

```bash
notebook/CC_Initialisation.ipynb
```
automates:
* EC2 instance creation
* DynamoDB table setup
* SQS queue creation
* Application deployment

---

## Security Notice

AWS credentials must NEVER be hard-coded.

Credentials should be provided using:
* Environment variables
* IAM roles
* AWS configuration files

---

## Documentation

Detailed architecture explanations, performance analysis,
and system evaluation are available in:

```bash
* docs/Report.pdf
* docs/Instructions.pdf
```
---

## Author

Yasser El Karkouri  
Cloud Computing Project  
Cranfield University