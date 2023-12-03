from unittest                       import TestCase

from osbot_utils.utils.Dev import pprint

import docker_images
from osbot_docker.apis.Docker_Image import Docker_Image
from osbot_utils.utils.Files        import path_combine, folder_exists, file_exists, folders_in_folder, folders_names
from osbot_docker.apis.API_Docker   import API_Docker
from osbot_utils.utils.Misc         import lower, random_string


class test_API_Docker(TestCase):

    def setUp(self):
        self.api_docker = API_Docker()
        self.path_docker_images = docker_images.folder
        print()

    def test__setUp(self):
        assert folder_exists(self.path_docker_images)
        assert folders_names(folders_in_folder(self.path_docker_images)) == ['__pycache__', 'centos', 'lambda_python__3_11', 'scratch']

    def test_client_api(self):
        assert type(self.api_docker.client_api()).__name__ == 'APIClient'

    def test_client_docker(self):
        assert type(self.api_docker.client_docker()).__name__ == 'DockerClient'

    def test_container_run(self):
        api_version = self.api_docker.client_api_version()
        error_bad_tag =  self.api_docker.container_run(image_name='hello-world', tag='bbbb').get('error')
        assert error_bad_tag == ('404 Client Error for '
                                 f'http+docker://localhost/v{api_version}/images/create?tag=bbbb&fromImage=hello-world: '
                                 'Not Found ("manifest for hello-world:bbbb not found: manifest unknown: '
                                 'manifest unknown")')

        error_bad_image_name = self.api_docker.container_run(image_name='aaaa', tag='bbbb').get('error')
        assert error_bad_image_name == ('404 Client Error for '                            
                                        f'http+docker://localhost/v{api_version}/images/create?tag=bbbb&fromImage=aaaa: '
                                        'Not Found ("pull access denied for aaaa, repository does not '
                                        "exist or may require 'docker login': denied: requested access to the "
                                        'resource is denied")')

        image_name = 'hello-world'
        tag        = 'latest'
        container  = self.api_docker.container_run(image_name=image_name, tag=tag)
        assert 'Hello from Docker!' in container.get('output')

        containers_hello_world = self.api_docker.containers_all__with_image(image_name,tag)
        for container in containers_hello_world:
            short_id = container.short_id()
            print(f"deleting container: {short_id} with image {image_name}:{tag}")
            assert container.delete() is True

    def test_containers(self):
        container = self.api_docker.container_create('hello-world')
        containers = self.api_docker.containers_all__by_id()
        assert container.short_id() in containers
        assert container.delete() is True

    def test_docker_params_append_options(self):
        docker_params = ['run']
        options        = {'key': '-v', 'value':'/a:/b'}
        result         = self.api_docker.docker_params_append_options(docker_params=docker_params,options=options)
        assert result == ['run', '-v','/a:/b']

        options        = [{'key': '-v', 'value':'/c:/d'}, {'key': '-v', 'value':'/e:/f'}]
        result         = self.api_docker.docker_params_append_options(docker_params, options)
        assert result == ['run', '-v', '/a:/b', '-v', '/c:/d', '-v', '/e:/f']

    def test_image_build(self):
        target_image       = 'centos'
        folder_docker_file = path_combine(self.path_docker_images, target_image)
        path_dockerfile    = path_combine(folder_docker_file, 'Dockerfile')
        image_name         = "osbot_docker__test_image_build"
        tag                = "abc"
        #image_name         = f"{repository}:{tag}"

        assert folder_exists(folder_docker_file)
        assert file_exists(path_dockerfile)
        docker_image = Docker_Image(image_name, tag, self.api_docker)
        result = docker_image.build(folder_docker_file)

        build_logs = result.get('build_logs')
        image      = result.get('image')
        status     = result.get('status')
        tags       = result.get('tags')
        assert docker_image.exists() is True
        assert status           == 'ok'
        assert image_name       in self.api_docker.images_names()
        assert image.get('Os')  == 'linux'
        assert next(build_logs) == {'stream': 'Step 1/3 : FROM centos:8'}

        assert docker_image.delete() is True

        assert image_name not in self.api_docker.images_names()

        for container in self.api_docker.containers_all():          # todo: figure out better way to do this
            labels = container.labels()
            vendor = labels.get('org.label-schema.vendor')
            if vendor == 'CentOS':
                short_id = container.short_id()
                print(f"deleting container: {short_id} since it has vendor=='{vendor}'")
                assert container.delete() is True

    def test_image_build__bad_data(self):
        assert Docker_Image(None         , None).build(None).get('error') == 'Either path or fileobj needs to be provided.'
        assert Docker_Image(None         , None).build(''  ).get('error')  == 'You must specify a directory to build in path'

        # todo: find out why in GH Actions the line below throws the error: AttributeError: 'APIError' object has no attribute 'msg'
        #assert self.api_docker.image_build(temp_folder(), None).get('exception').msg.get('message') == 'Cannot locate specified Dockerfile: Dockerfile'

    def test_image_build_scratch(self):
        path         = path_combine(self.path_docker_images, 'scratch')
        repository   = 'scratch'
        tag          = 'latest'
        result       = Docker_Image(image_name=repository, image_tag=tag).build(path)
        image        = result.get('image')
        container_id = image.get('Container')
        assert self.api_docker.container(container_id).exists() is False

    def test_image_info(self):
        assert Docker_Image(random_string()).info() == {}

    def test_image_exists(self):
        assert Docker_Image(random_string()).exists()  is False

    def test_image_pull(self):
        image_name = 'centos'
        tag        = '8'
        image      = Docker_Image(image_name,tag)
        assert image.pull() is True
        image_info = image.info()
        assert image_info.get('RepoTags') == ['centos:8']
        assert self.api_docker.container_run(image_name, tag, "pwd"                    ) == {'output': '/'                            , 'status': 'ok'}
        result = self.api_docker.container_run(image_name, tag, "cat /etc/redhat-release")
        assert result.get('status') == 'ok'
        assert 'CentOS Linux release 8' in result.get('output')

        containers_centos = self.api_docker.containers_all__with_image(image_name, tag)
        for container in containers_centos:
            short_id = container.short_id()
            print(f"deleting container: {short_id} with image {image_name}:{tag}")
            assert container.delete() is True


    def test_images(self):
        images = self.api_docker.images()
        assert len(images) > 0

    def test_images_names(self):
        names = self.api_docker.images_names()
        assert 'hello-world' in names

    def test_server_info(self):
        server_info = self.api_docker.server_info()
        assert 'KernelMemory' in server_info
        assert lower(server_info.get('OSType')) == 'linux'
