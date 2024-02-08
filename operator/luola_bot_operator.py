from kubernetes import client,config
import base64
import time
import logging
import sys

def fetch_bot_secret(secret, namespace, data):
    encoded_secret = client.CoreV1Api().read_namespaced_secret(secret, namespace).data[data]
    return base64.b64decode(encoded_secret).decode("utf-8").replace('\n', '')

def new_luola_bot_secret(luola_bot_resource):
    name = luola_bot_resource["metadata"]["name"]
    namespace = luola_bot_resource["metadata"]["namespace"]
    token = fetch_bot_secret(luola_bot_resource["spec"]["botTokenSecret"], namespace, "token")
    data = f'token: "{token}"'
    if "disable_default_db_api" in luola_bot_resource["spec"].keys():
        data = f'{data}\ndisable_default_db_api: {luola_bot_resource["spec"]["disable_default_db_api"]}'
    if "db_apis" in luola_bot_resource["spec"].keys():
        data = f'{data}\ndb_apis:'
        for api in luola_bot_resource["spec"]["db_apis"]:
            data = f'{data}\n  - url: {api["url"]}'
            if ("username" in api.keys()) and ("passwordSecret" in api.keys()):
                pw = fetch_bot_secret(api["passwordSecret"], namespace, "password")
                data = f'{data}\n    username: {api["username"]}\n    password: {pw}'
    if "privileged_users" in luola_bot_resource["spec"].keys():
        data = f'{data}\nprivileged_users:'
        for user in luola_bot_resource["spec"]["privileged_users"]:
            data = f'{data}\n  - {user}'
    return client.V1Secret(
        api_version = "v1",
        kind = "Secret",
        metadata = client.V1ObjectMeta(
            name = name,
            namespace = namespace,
            labels = {"app": name}
        ),
        data = {"luolabot.yaml": base64.b64encode(bytes(data, "utf-8")).decode("utf-8")}
    )

def new_luola_bot_deployment(luola_bot_resource):
    return client.V1StatefulSet(
        api_version = "apps/v1",
        kind = "Deployment",
        metadata = client.V1ObjectMeta(
            name = luola_bot_resource["metadata"]["name"],
            namespace = luola_bot_resource["metadata"]["namespace"],
            labels = {"app": luola_bot_resource["metadata"]["name"]}
        ),
        spec = client.V1StatefulSetSpec(
            service_name = luola_bot_resource["metadata"]["name"],
            replicas = 1,
            selector = client.V1LabelSelector(
                match_labels = {"app": luola_bot_resource["metadata"]["name"]}
            ),
            template = client.V1PodTemplateSpec(
                metadata = client.V1ObjectMeta(                  
                    labels = {"app": luola_bot_resource["metadata"]["name"]}
                ),
                spec = client.V1PodSpec(
                    containers = [
                        client.V1Container(
                            name = "luolabot",
                            image = luola_bot_resource["spec"]["image"],
                            image_pull_policy = "Always",
                            command = [
                                "luolabot",
                                "--config",
                                "/etc/luolabot/luolabot.yaml",
                            ],
                            volume_mounts = [
                                client.V1VolumeMount(
                                    name = "luola-bot-config",
                                    mount_path = "/etc/luolabot",
                                    read_only = True
                                )
                            ]
                        )
                    ],
                    volumes = [
                        client.V1Volume(
                            name = "luola-bot-config",
                            secret = client.V1SecretVolumeSource(
                                secret_name = luola_bot_resource["metadata"]["name"],
                                items = [
                                    client.V1KeyToPath(
                                        key = "luolabot.yaml",
                                        path = "luolabot.yaml"
                                    )
                                ]
                            )
                        )
                    ],
                    tolerations = [
                        client.V1Toleration(
                            key = "node-role.kubernetes.io/master",
                            operator = "Exists",
                            effect = "NoSchedule"
                        ),
                        client.V1Toleration(
                            key = "node-role.kubernetes.io/control-plane",
                            operator = "Exists",
                            effect = "NoSchedule"
                        )
                    ]
                )
            )
        )
    )

def create_resource(resource_type, custom_resource, resource_api):
    logging.info("(Re-)Creating resource {}.".format(resource_type))
    new_resource_object_func = globals()["new_luola_bot_{}".format(resource_type)]
    new_resource = new_resource_object_func(custom_resource)
    resource_create_func = getattr(resource_api, "create_namespaced_{}".format(resource_type))
    resource_create_func(body=new_resource, namespace=custom_resource["metadata"]["namespace"])
    logging.info("Resource {} created.".format(resource_type))
    return True

def check_k8s_resource_and_create_if_missing(resource_type, custom_resource, resource_api, force_reconciliation=False):
    resource_list_func = getattr(resource_api, "list_namespaced_{}".format(resource_type))
    resources = resource_list_func(custom_resource["metadata"]["namespace"])
    deployment_exists = custom_resource["metadata"]["name"] in [resource.metadata.name for resource in resources.items]
    if deployment_exists and force_reconciliation:
        resource_del_func = getattr(resource_api, "delete_namespaced_{}".format(resource_type))
        resource_del_func(name=custom_resource["metadata"]["name"], namespace=custom_resource["metadata"]["namespace"])
        return create_resource(resource_type, custom_resource, resource_api)
    elif not deployment_exists:
        return create_resource(resource_type, custom_resource, resource_api)
    else:
        logging.info("No need to do anything about resource {}.".format(resource_type))
        return False
    
def main():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    logging.info("Starting luolaBot operator.")

    logging.info("Loading kube config.")
    config.load_kube_config()

    core_api = client.CoreV1Api()
    app_api = client.AppsV1Api()

    while True:
        deployments = app_api.list_deployment_for_all_namespaces()
        operator_namespace = "default"
        for deployment in deployments.items:
            if "luolabot-operator" in deployment.metadata.name:
                namespace = deployment.metadata.namespace
                break
    
        custom_object_api = client.CustomObjectsApi()
        luola_bot_resources = custom_object_api.list_cluster_custom_object(group="luolabot.tg", version="v1", plural="luolabots")
    
        if "items" in luola_bot_resources.keys():
            logging.info("Found following luolabot custom resources: {}".format(luola_bot_resources["items"]))
            for luola_bot_resource in luola_bot_resources["items"]:

                reconciled_resources = []
                
                #Config
                if check_k8s_resource_and_create_if_missing("secret", luola_bot_resource, core_api):
                    reconciled_resources.append("secret")

                #Deployment
                force_deployment_reconciliation = False
                if "secret" in reconciled_resources:
                    force_deployment_reconciliation = True
                if check_k8s_resource_and_create_if_missing("deployment", luola_bot_resource, app_api, force_reconciliation=force_deployment_reconciliation):
                    reconciled_resources.append("deployment")

        sleep_time=15
        logging.info("Sleeping {} seconds before next check for new luolabot custom resources.".format(sleep_time))
        time.sleep(sleep_time)

if __name__ == '__main__':
    main()
