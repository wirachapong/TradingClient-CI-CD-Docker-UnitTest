# TradingClient-CI-CD-Docker-UnitTest

## Overview

This project is a production-ready client capable of placing market buy/sell orders for the BTC/USDT pair on two cryptocurrency exchanges, Binance and Bybit. The client automatically selects the exchange with the best price to execute the order.

The client is implemented in Python, with integration written from scratch through APIs provided by Binance and Bybit. The project includes unit tests, CI/CD configuration, and Docker setup for environment consistency and ease of deployment.

## Project Structure

Here is a brief overview of the primary files and folders in the repository:

- **.github/workflows/ci.yml**: GitHub Actions workflow file to automatically run tests on each push or pull request.

- **exchange/**: Contains the API client integrations for Binance and Bybit.
  - **binance_client.py**: Python module for interacting with the Binance API, including order placement and price retrieval.
  - **bybit_client.py**: Python module for interacting with the Bybit API, with similar functionality to the Binance client.
  - **test-prv-key.pem** and **test-pub-key.pem**: Private and public key files used for encrypted communication with exchanges.

- **tests/**: Contains all unit tests for the project.
  - **test_binance_client.py**: Unit tests for the Binance client integration.
  - **test_bybit_client.py**: Unit tests for the Bybit client integration.
  - **test_client.py**: Unit tests for the main `TradingClient` class, which coordinates API interactions.

- **client.py**: Main module for the `TradingClient` class, which contains methods to get the best price and place orders.

- **Dockerfile**: Docker setup for building and running the project within a consistent environment.

- **requirements.txt**: Python dependencies for the project.

## Setup Instructions

### Prerequisites

- **Docker installed on your local machine**
- **A GitHub account for accessing secrets if you want to run CI/CD on GitHub Actions**
- **API keys (and/or Password) for Binance and Bybit test environments**
  - Binance: RSA key is used in the current code version and it's private key file is stored in the exchange folder. The private key file is locked without a password.  

## Running the Project with Docker

#### 1. Clone the Repository
   ```bash
   git clone https://github.com/yourusername/TradingClient-CI-CD-Docker-UnitTest.git
   cd TradingClient-CI-CD-Docker-UnitTest
   ```

#### 2. Prepare the environment
<<<<<<< HEAD
In a CI/CD environment, such as GitHub Actions, the .env file will not be present. Instead, GitHub Secrets will have to be set up to supply environment variables directly. Therefore, the line below is commented out to ensure it doesn’t cause errors in environments where the .env file is absent. 

If you are running the project locally, you will need to create a .env file with the necessary variables, uncomment the line below in the Dockerfile, and then rebuild the image.
=======
In a CI/CD environment, such as GitHub Actions, the .env file will not be present. Instead, GitHub Secrets will have to be set up to supply environment variables directly. Therefore, the line below is commented out to ensure it doesn’t cause errors in environments where the .env file is absent. Also ensure that .env is also included in your .dockerignore.

If you are running the project locally, you will need to create a .env file with the necessary variables, uncomment the line below in the Dockerfile, and then rebuild the image. Also ensure that .env is not present in your .dockerignore.

>>>>>>> e342ad0 (Update README.md)
   ```bash
   COPY .env .env
   ```

#### 3. Build the Docker Image
   ```bash
   docker build -t my_trading_client .
   ```

#### 4. Run the Docker Container
   ```bash
   docker run my_trading_client
   ```

## Possible Improvement

- The actual logic for deciding whether to buy/sell from certain exchanges will be much more complicated if the order volume is significant. The proper logic is to call the orderbook APIs of the exchanges and combine the databook data together and calculate the optimal amount that should be buy/sell from each exchanges.
  - We assumed that the value of users' order in the current version of code is not too significant.


