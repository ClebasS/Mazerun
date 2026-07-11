# 🏛️ Labyrinth Monitoring Platform

A distributed real-time monitoring platform developed as part of the **Distributed Information Systems Project** at **ISCTE – Instituto Universitário de Lisboa**.

The project integrates **MQTT**, **MongoDB**, **MySQL**, **Python**, **PHP**, and **Flutter** to monitor a labyrinth game, process sensor data, detect abnormal situations, generate alerts, and provide real-time information through both a Web interface and an Android application.

---

# 📖 Overview

The platform receives movement and sound data generated during the execution of a labyrinth game. These messages are transmitted through MQTT, processed by distributed services, validated according to the game rules, and stored in different databases depending on their purpose.

The system is divided into two main processing nodes:

* **PC1** – Responsible for receiving MQTT messages, validating their structure, storing them in MongoDB, and forwarding them to PC2.
* **PC2** – Responsible for validating game logic, detecting anomalies, generating alerts, calculating the score, and updating the MySQL database.

The application also provides both a Web management interface and an Android application for monitoring the game in real time.

---

# ✨ Features

* Real-time MQTT communication
* MongoDB Replica Set
* Automatic migration from MongoDB to MySQL
* Multi-threaded architecture
* Producer-consumer processing model
* Automatic score calculation
* Noise monitoring
* Movement monitoring
* Automatic alert generation
* Invalid data detection
* Noise outlier detection
* Automatic door control
* Android application
* Web administration panel
* Stored Procedures and Triggers
* Automatic thread supervision
* Automatic game recovery after failures

---

# 🏗️ System Architecture

```text
                MazeRun

                   │
                   ▼

             MQTT Broker
                   │
                   ▼

        ┌──────────────────┐
        │       PC1        │
        │                  │
        │ MQTT Receiver    │
        │ MongoDB Storage  │
        │ Migration Thread │
        │ Supervisor       │
        └──────────────────┘
                   │
             MQTT Broker
                   │
                   ▼
        ┌──────────────────┐
        │       PC2        │
        │                  │
        │ MQTT Receiver    │
        │ Validation       │
        │ Game Logic       │
        │ Alert Engine     │
        │ MySQL            │
        │ Supervisor       │
        └──────────────────┘
            │           │
            ▼           ▼
       Web Application  Android App
```

---

# 🛠️ Technologies

## Programming Languages

* Python
* Dart
* PHP
* SQL

## Frameworks

* Flutter
* Android SDK

## Databases

* MongoDB
* MySQL

## Communication

* MQTT
* Mosquitto
* JSON

## Development Tools

* Android Studio
* Visual Studio Code
* XAMPP
* phpMyAdmin
* Git

---

# 📂 Project Structure

```text
Project
│
├── Android/
├── Flutter/
├── PHP/
├── Python/
├── SQL/
├── MongoDB/
├── Documentation/
└── README.md
```

---

# ⚙️ Main Components

## PC1

PC1 is responsible for collecting data from the game and preparing it for processing.

Main responsibilities:

* Subscribe to MQTT topics
* Receive movement messages
* Receive sound messages
* Validate message structure
* Store valid data in MongoDB
* Archive processed documents
* Publish validated messages to MQTT
* Supervise worker threads

---

## PC2

PC2 implements the complete business logic of the game.

Main responsibilities:

* Receive migrated MQTT messages
* Validate every movement
* Validate sound measurements
* Detect invalid sensor readings
* Detect statistical outliers
* Update the labyrinth state
* Calculate the score
* Open and close doors
* Generate alerts
* Update MySQL
* Supervise worker threads

---

# 🧵 Multithreading

The system relies on multiple concurrent threads to reduce latency and improve reliability.

The architecture includes:

* MQTT receiver threads
* Migration threads
* Producer thread
* Consumer thread
* Alert processing
* Thread supervision

Movement processing follows a **Producer–Consumer** model:

1. One thread continuously receives MQTT movement messages.
2. Messages are placed into a blocking queue.
3. A second thread removes messages from the queue.
4. The message is validated.
5. The labyrinth state is updated.
6. Score conditions are evaluated immediately.

This design minimizes the delay between receiving a movement and updating the game state.

---

# 🗄️ Databases

## MongoDB

MongoDB is used as the first storage layer.

Collections:

* Movements
* Sound
* Movements_Archived
* Sound_Archived
* Discarded_Data

Each document contains a **migrated** flag indicating whether it has already been forwarded to the second processing stage.

---

## MySQL

MySQL stores the processed game state.

Main entities include:

* Games
* Alerts
* Sound Measurements
* Movement Measurements
* Labyrinth Occupancy
* Marsamis
* Users

The application communicates with MySQL exclusively through Stored Procedures.

---

# 📡 MQTT Communication

Two MQTT topics are used throughout the system:

* Movement messages
* Sound messages

Different Quality of Service (QoS) levels are used depending on the message type.

* **QoS 2** for movement messages to guarantee exactly-once delivery.
* **QoS 1** for sound messages to balance reliability and performance.

The `migrated` field is updated only after the MQTT broker confirms successful delivery.

---

# 🧠 Game Logic

The game engine validates every received movement before updating the game state.

Examples of validations include:

* Game must be running.
* The Marsami must be located in the reported origin room.
* The destination room must be connected through a valid corridor.
* Tired Marsamis cannot move.
* Invalid timestamps are rejected.
* Invalid movements never affect the game state.

---

# 🔊 Noise Processing

Noise processing consists of several stages.

## Invalid Data Detection

Messages with invalid formats or inconsistent values are identified and marked as invalid.

Instead of deleting invalid data, the system stores it for future analysis.

---

## Outlier Detection

The project implements statistical outlier detection using the **Tukey Interquartile Range (IQR)** method.

When fewer than twenty measurements are available, a temporary acceptance interval is calculated using:

* Normal Noise Level
* Noise Tolerance
* Safety Margin

After enough samples are collected, the IQR method becomes the primary detection algorithm.

Detected outliers are marked as invalid but remain stored in the database.

---

# 🚨 Alert System

The platform automatically generates alerts whenever abnormal situations occur.

Three alert categories are implemented:

### 🔴 Danger

Critical situations requiring immediate action.

Examples:

* Excessive noise
* Critical system conditions

---

### 🟡 Warning

Abnormal situations that should be monitored.

Examples:

* Consecutive invalid readings
* High percentage of invalid data
* Noise outliers

---

### 🔵 Information

General game events.

Examples:

* Doors reopened
* Game finished
* Normal conditions restored

To avoid alert flooding, users can configure a minimum interval between visible alerts.

---

# 🚪 Score Calculation

The score is based on the distribution of even and odd Marsamis inside each room.

Whenever the number of even Marsamis equals the number of odd Marsamis:

1. The room doors are closed.
2. A safety delay is applied.
3. The balance is verified again.
4. If the balance still exists, the score is awarded.
5. Doors are reopened.

This strategy minimizes race conditions caused by message latency.

---

# 🔒 Reliability

Several mechanisms were implemented to improve reliability.

* MongoDB Replica Set
* Thread supervision
* Automatic thread restart
* MQTT acknowledgements
* Game recovery after interruptions
* Persistent MQTT sessions
* Blocking queues
* Multi-threaded processing

These mechanisms ensure that the platform continues operating even when temporary failures occur.

---

# 🔐 Security

Database access is controlled through dedicated MySQL users and roles.

All database operations are executed using Stored Procedures instead of direct SQL statements.

This approach improves security while enforcing the game rules inside the database itself.

---

# 🚀 Getting Started

## Requirements

* Python 3.x
* Flutter SDK
* Android Studio
* MongoDB
* MySQL
* MQTT Broker (Mosquitto or compatible)
* XAMPP (for PHP Web Application)

## Installation

1. Clone the repository.

```bash
git clone https://github.com/yourusername/Mazerun.git
```

2. Configure MongoDB.

3. Configure MySQL and import the SQL scripts.

4. Configure the MQTT broker.

5. Update the configuration files with your database and broker credentials.

6. Start the PC1 services.

7. Start the PC2 services.

8. Run the Web application.

9. Launch the Android application.

---

# 🎯 Project Objectives

This project demonstrates the implementation of a distributed real-time system capable of:

* Processing sensor data
* Managing concurrent operations
* Synchronizing heterogeneous databases
* Detecting abnormal events
* Generating real-time alerts
* Maintaining game consistency
* Providing fault-tolerant operation

It combines distributed systems, databases, networking, concurrency, and mobile application development into a single integrated platform.
