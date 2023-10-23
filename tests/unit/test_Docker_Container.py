from unittest import TestCase

from osbot_utils.utils.Dev import pprint

from osbot_docker.API_Docker import API_Docker


class test_Docker_Container(TestCase):

    def setUp(self) -> None:
        self.api_docker       = API_Docker()
        self.image_name       = 'hello-world'
        self.tag              = 'latest'
        self.docker_container = self.api_docker.container_create(image_name=self.image_name, tag=self.tag)

    def tearDown(self) -> None:
        assert self.docker_container.delete() is True


    def test_exists(self):
        assert self.docker_container.exists() is True

