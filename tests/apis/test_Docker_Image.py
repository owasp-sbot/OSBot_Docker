from unittest import TestCase

from osbot_docker.apis.Docker_Image import Docker_Image
from osbot_utils.utils.Dev import pprint

from osbot_docker.apis.API_Docker import API_Docker


class test_Docker_Image(TestCase):

    def setUp(self):
        self.api_docker = API_Docker()
        self.image_name = 'hello-world'
        self.image_tag  = 'latest'
        self.image      = Docker_Image(image_name=self.image_name, image_tag=self.image_tag, api_docker=self.api_docker)
        pass

    def teardown(self):
        pass

    def test__api_docker__images_names(self):
        images = self.api_docker.images_names()
        assert self.image_name in images

    def test_info(self):
        info = self.image.info()
        assert 'Architecture' in info
        assert info.get('Tags') == [f"{self.image_name}:{self.image_tag}"]

        bad_image = Docker_Image('aaaa-not-exits-bbb', 'aaaa-bbbb')
        assert bad_image.info  () == {}
        assert bad_image.exists() is False

    def test_pull(self):
        assert self.image.pull  () is True
        assert self.image.exists() is True
        assert self.image.delete() is True
        assert self.image.exists() is False
        assert self.image.pull  () is True
        assert self.image.exists() is True

