import docker

def get_logs(container_name):
    client = docker.DockerClient(base_url='tcp://host.docker.internal:2375')
    try:
        container = client.containers.get(container_name)
        return container.logs(tail=100).decode('utf-8').splitlines()
    except Exception as e:
        return [f"Error: {str(e)}"]
