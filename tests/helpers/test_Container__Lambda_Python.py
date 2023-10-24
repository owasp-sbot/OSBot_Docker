from unittest import TestCase

from osbot_docker.apis.Docker_Container import Docker_Container
from osbot_utils.utils.Dev import pprint

from osbot_docker.helpers.Container__Lambda_Python import Container__Lambda_Python


class test_Container__Lambda_Python(TestCase):

    def test__enter__exit(self):
        print()
        with Container__Lambda_Python() as _:
            assert _.container.exists() is True
            print(_.container.logs())
            assert _.invoke(               ) == 'docker - hello world!'
            assert _.invoke({'name':'aaaa'}) == 'docker - hello aaaa!'

        assert _.container.exists() is False

    def test_docker_setup(self):
        container_id = 'd8d90564323a'
        container = Docker_Container(container_id=container_id)
        pprint(container.info_raw())