# Kubernetes Benchmarking Automation

## Main Goal

This project aims to automate the benchmarking process in a Kubernetes environment by collecting deployment logs to calculate various metrics such as average server load, motion count, number of samples, and queue size. These metrics help in assessing the performance of Kubernetes deployments.

## Processes

 - **Log Collection**: Deployment logs are captured in real-time to gather data for metric calculations.
 - **Metric Calculations**: Various performance metrics are calculated from the collected logs, focusing on server load, motion detection counts, sample numbers, and queue sizes.
 - **Results Reporting**: Calculated metrics are written to CSV files for easy analysis and record-keeping.

## Project Structure

 - **bench.py**: Orchestrates the benchmarking process, including log collection and metric calculation.
 - **k8s.py**: Interfaces with Kubernetes to capture logs from specified deployments.
 - **calculations.py**: Contains the logic for computing specific metrics from log data.
 - **cleanup.py**: Cleans up log files post-benchmarking.
 - **deployment_processing.py**: Processes the log data to calculate and report metrics.
 - **logg.py**, **hw.py**, **hw.sh**: Support logging and hardware metrics collection.
 - **Dockerfile**: Specifies the environment for running the benchmarking scripts.
 - **bench.yaml**: Defines the Kubernetes cron job for scheduling benchmarking tasks.

## Docker Image and Kubernetes Cron Job

**Docker Image**: Contains all necessary scripts and dependencies to run the benchmarking tasks. It's built and pushed to a Docker registry using the following commands:

```
docker build --platform=linux/amd64 -t tikpapyan/benchmarking:v1.0.0 .
docker push tikpapyan/benchmarking:v1.0.0
```

**Kubernetes Cron Job (`bench.yaml`)**: Schedules the benchmarking tasks within a Kubernetes environment. It includes configurations for service accounts, roles, and the cron job setup to periodically initiate the benchmarking process.

## Building and Deployment

1. **Build Docker Image**: Use the provided Dockerfile to build the image containing the benchmarking environment.
2. **Push to Registry**: Upload the built image to a Docker registry.
3. **Deploy on Kubernetes**: Apply the bench.yaml file to your Kubernetes cluster to set up the necessary roles, permissions, and scheduled tasks.
