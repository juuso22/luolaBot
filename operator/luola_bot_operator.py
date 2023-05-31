from kubernetes import client,config
import base64
import time

def fetch_bot_token(bot_resource):
    encoded_token = client.CoreV1Api().read_namespaced_secret(bot_resource["spec"]["botTokenSecret"], bot_resource["metadata"]["namespace"]).data["token"]
    return base64.b64decode(encoded_token)

def new_luola_bot_secret(luola_bot_resource):
    token = fetch_bot_token(luola_bot_resource).decode("utf-8").replace('\n', '')
    data = '''token: "{}"
instances:'''.format(token)
    for i in range(0, luola_bot_resource["spec"]["replicas"]):
        data = '''{data}
- {bot}-{i}.{bot}'''.format(data=data, bot=luola_bot_resource["metadata"]["name"], i=i)
    return client.V1Secret(
        api_version = "v1",
        kind = "Secret",
        metadata = client.V1ObjectMeta(
            name = luola_bot_resource["metadata"]["name"],
            namespace = luola_bot_resource["metadata"]["namespace"],
            labels = {"app": luola_bot_resource["metadata"]["name"]}
        ),
        data = {"luolabot.yaml": base64.b64encode(bytes(data, "utf-8")).decode("utf-8")}
    )

def new_luola_bot_service(luola_bot_resource):
    return client.V1Service(
        api_version = "v1",
        kind = "Service",
        metadata = client.V1ObjectMeta(
            name = luola_bot_resource["metadata"]["name"],
            namespace = luola_bot_resource["metadata"]["namespace"],
            labels = {"app": luola_bot_resource["metadata"]["name"]}
        ),
        spec = client.V1ServiceSpec(
            ports = [
                client.V1ServicePort(
                    port = 7175,
                    name = "internal"
                )
            ],
            cluster_ip = None,
            selector = {"app": "{}".format(luola_bot_resource["metadata"]["name"])}
        )
    )

def new_luola_bot_stateful_set(luola_bot_resource):
    return client.V1StatefulSet(
        api_version = "apps/v1",
        kind = "StatefulSet",
        metadata = client.V1ObjectMeta(
            name = luola_bot_resource["metadata"]["name"],
            namespace = luola_bot_resource["metadata"]["namespace"],
            labels = {"app": luola_bot_resource["metadata"]["name"]}
        ),
        spec = client.V1StatefulSetSpec(
            service_name = luola_bot_resource["metadata"]["name"],
            replicas = luola_bot_resource["spec"]["replicas"],
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

def check_k8s_resource_and_create_if_missing(resource_type, custom_resource, resource_api):
    resource_list_func = getattr(resource_api, "list_namespaced_{}".format(resource_type))
    resources = resource_list_func(custom_resource["metadata"]["namespace"])
    if not custom_resource["metadata"]["name"] in [resource.metadata.name for resource in resources.items]:
        print("No resource {} was found, need to reconcile.".format(resource_type))
        new_resource_object_func = globals()["new_luola_bot_{}".format(resource_type)]
        new_resource = new_resource_object_func(custom_resource)
        resource_create_func = getattr(resource_api, "create_namespaced_{}".format(resource_type))
        resource_create_func(body=new_resource, namespace=custom_resource["metadata"]["namespace"])
        print("Resource {} reconciled.".format(resource_type))
    else:
        print("Resource {} was found, no need to reconcile.".format(resource_type))
    
def main():
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
            for luola_bot_resource in luola_bot_resources["items"]:

                #Config
                check_k8s_resource_and_create_if_missing("secret", luola_bot_resource, core_api)

                #Service
                check_k8s_resource_and_create_if_missing("service", luola_bot_resource, core_api)

                #Stateful set
                check_k8s_resource_and_create_if_missing("stateful_set", luola_bot_resource, app_api)

        time.sleep(60)

if __name__ == '__main__':
    main()
