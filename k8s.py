#!/usr/bin/env python3

import os
import time
import threading

from kubernetes import client, config, watch, stream
from logg import logger


def get_kubernetes_api_client():
    config.load_incluster_config()
    core_v1_api = client.CoreV1Api()
    apps_v1_api = client.AppsV1Api()
    return core_v1_api, apps_v1_api


def capture_logs_from_pods_of_deployment(core_v1_api, deployment, namespace, duration, log_dir):
    selector = ','.join([f'{k}={v}' for k, v in deployment.spec.selector.match_labels.items()])
    pods = core_v1_api.list_namespaced_pod(namespace, label_selector=selector)

    end_time = time.time() + duration

    for pod in pods.items:
        log_file_path = os.path.join(log_dir, f"{pod.metadata.name}.log")
        try:
            with open(log_file_path, 'w') as log_file:
                w = watch.Watch()
                for log_line in w.stream(core_v1_api.read_namespaced_pod_log, name=pod.metadata.name, namespace=namespace):
                    if time.time() > end_time:
                        break
                    log_file.write(log_line + '\n')
                    log_file.flush()

        except client.exceptions.ApiException as e:
            logger.error(f"API exception in capturing logs for pod {pod.metadata.name} in namespace {namespace}: {e}")
        except IOError as io_err:
            logger.error(f"I/O error writing to file '{log_file_path}': {io_err}")
        except Exception as e:
            logger.error(f"Exception in capturing logs for pod {pod.metadata.name} in namespace {namespace}: {e}")


def capture_logs(namespace, duration, log_dir):
    core_v1_api, apps_v1_api = get_kubernetes_api_client()

    try:
        deployments = apps_v1_api.list_namespaced_deployment(namespace)
        for deployment in deployments.items:
            pod_log_thread = threading.Thread(target=capture_logs_from_pods_of_deployment, 
                                              args=(core_v1_api, deployment, namespace, duration, log_dir))
            pod_log_thread.start()

            if deployment.metadata.name.startswith("ids"):
                logger.debug("Capturing additional IDS info logs.")
                ids_info_log_thread = threading.Thread(target=capture_ids_info_logs, 
                                                       args=(core_v1_api, deployment, namespace, duration, log_dir))
                ids_info_log_thread.start()
                ids_info_log_thread.join()

            pod_log_thread.join()

    except client.exceptions.ApiException as e:
        logger.error(f"API exception while listing deployments in namespace {namespace}: {e}")
    except Exception as e:
        logger.error(f"Exception while processing namespace {namespace}: {e}")


def capture_ids_info_logs(core_v1_api, deployment, namespace, duration, log_dir):
    try:
        if duration > 1:
            time.sleep(duration - 1)

        label_selector = ','.join([f'{k}={v}' for k, v in deployment.spec.selector.match_labels.items()])
        pods = core_v1_api.list_namespaced_pod(namespace, label_selector=label_selector)

        for pod in pods.items:
            command = ["cat", "/var/log/ids/scylla-info.log"]
            resp = stream.stream(core_v1_api.connect_get_namespaced_pod_exec,
                                 name=pod.metadata.name,
                                 namespace=namespace,
                                 command=command,
                                 stderr=True,
                                 stdin=False,
                                 stdout=True,
                                 tty=False)

            info_log_path = os.path.join(log_dir, f"info-{pod.metadata.name}.log")
            with open(info_log_path, 'w') as info_log_file:
                info_log_file.write(resp)

    except Exception as e:
        logger.error(f"Error in capture_ids_info_logs: {e}")

