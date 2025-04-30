import docker

def get_metrics():
    client = docker.DockerClient(base_url='tcp://host.docker.internal:2375')
    containers = client.containers.list()
    metrics = []
    for c in containers:
        stats = c.stats(stream=False)
        mem = stats['memory_stats']
        cpu = stats['cpu_stats']
        metrics.append({
            'name': c.name,
            'status': c.status,
            'memory_usage': mem['usage'],
            'memory_limit': mem.get('limit', 0),
            'cpu_total': cpu['cpu_usage']['total_usage'],
            'system_cpu': cpu.get('system_cpu_usage', 0),
        })
    return metrics
