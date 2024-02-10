from osbot_docker.helpers.Docker_Lambda__Python import Docker_Lambda__Python


class Container__Lambda_Python:

    def __init__(self):
        self.docker_lambda__python = Docker_Lambda__Python()
        self.container             = None

    def __enter__(self):
        self.container = self.docker_lambda__python.create_container()
        self.container.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.stop()
        self.container.delete()

    def invoke(self, payload=None):
        return self.docker_lambda__python.invoke(payload=payload)

