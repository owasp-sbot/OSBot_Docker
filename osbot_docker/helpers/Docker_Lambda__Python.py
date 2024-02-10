import requests

from osbot_docker.apis.Docker_Image import Docker_Image
from osbot_utils.utils.Files import path_combine, file_contents

import docker_images


class Docker_Lambda__Python:

    def __init__(self, host_port=9000):
        self.host_port     = host_port
        self.image_name    = 'lambda_python__3_11'
        self.api_docker    = None
        self.docker_image  = Docker_Image(self.image_name, 'latest')
        self.port_bindings = { 8080: self.host_port }

    def create_container(self):
        return self.docker_image.create_container(port_bindings=self.port_bindings)

    def image_build(self):
        return self.docker_image.build(self.path_lambda_python())

    def invoke(self, payload):
        url      = f"http://localhost:{self.host_port}/2015-03-31/functions/function/invocations"
        response = requests.post(url=url, json=payload or {})
        return response.json()

    def dockerfile(self):
        return file_contents(self.path_docker_dockerfile())

    def path_docker_dockerfile(self):
        return path_combine(self.path_lambda_python(), 'Dockerfile')

    def path_docker_images(self):
        return docker_images.folder

    def path_lambda_python(self):
        return path_combine(docker_images.folder, self.image_name)
