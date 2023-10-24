from unittest import TestCase

from osbot_utils.utils.Dev import pprint

import docker_images
from osbot_docker.helpers.Docker_Lambda__Python import Docker_Lambda__Python
from osbot_utils.utils.Files                    import path_combine, folder_exists, file_exists


class test_Docker_Lambda__Python(TestCase):

    def setUp(self):
        self.docker_lambda__python = Docker_Lambda__Python()
        pass

    def teardown(self):
        pass

    def test_create_container(self):
        container = self.docker_lambda__python.create_container()
        assert container.exists() is True
        assert container.info().get('image') == f"{self.docker_lambda.image_name}:latest"
        assert container.status() == 'created'
        assert container.start() is True
        assert container.status() == 'running'
        assert "(rapid) exec '/var/runtime/bootstrap' (cwd=/var/task, handler=)" in container.logs()
        assert container.stop() is True
        assert container.status() == 'exited'
        assert container.delete() is True

    def test_image_build(self):
        result = self.docker_lambda__python.image_build()
        assert result.get('status') == 'ok'

    def test_dockerfile(self):
        assert self.docker_lambda__python.dockerfile().startswith('FROM public.ecr.aws/lambda/python:3.11')

    def test_path_docker_dockerfile(self):
        assert file_exists(self.docker_lambda__python.path_docker_dockerfile())

    def test_path_docker_images(self):
        assert self.docker_lambda__python.path_docker_images() == docker_images.folder
        assert folder_exists(self.docker_lambda__python.path_docker_images())

    def test_path_lambda_python(self):
        assert folder_exists(self.docker_lambda__python.path_lambda_python())