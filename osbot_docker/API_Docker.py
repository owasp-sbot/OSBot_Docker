import docker
from osbot_utils.utils.Process import exec_process

from osbot_utils.decorators.methods.cache_on_self import cache_on_self

from osbot_utils.decorators.methods.catch import catch

from osbot_utils.utils.Misc import trim, bytes_to_str


class API_Docker:

    def __init__(self, debug=False):
        self.debug              = debug
        self.docker_run_timeout = None

    @cache_on_self
    def client(self):
        return docker.from_env()

    @catch
    def container_run(self, repository, tag='latest', command=None, timeout=None):
        if tag:
            image = f"{repository}:{tag}"
        else:
            image = repository

        output = self.client().containers.run(image, command, timeout=timeout)
        return { 'status': 'ok'   , 'output' : trim(bytes_to_str(output)) }

    def containers(self):
        return self.client().containers.list()

    def docker_params_append_options(self, docker_params, options):
        if options:
            if type(options) is not list:                # todo: create decorator for this code pattern (i.e. make sure the value is a list)
                options = [options]
            for option in options:
                key   = option.get('key')
                value = option.get('value')
                docker_params.append(key)
                docker_params.append(value)
        return docker_params

    def docker_run(self, image_params, options=None, timeout=None):
        """Use this method to invoke the docker executable directly
            image_params is an image name of an array of image name + image params"""

        if image_params:
            if type(image_params) is str:
                image_params = [image_params]

        docker_params = ['run', '--rm']
        self.docker_params_append_options(docker_params, options)
        docker_params.extend(image_params)
        self.print_docker_comamnd(docker_params)                # todo: refactor to use logging class

        return exec_process('docker', docker_params, timeout=self.docker_run_timeout)

    def docker_run_bash(self, image_name, image_params, options=None, bash_binary='/bin/bash'):
        bash_params = [image_name, '-c']
        if type(image_params) is str:
            bash_params.append(image_params)
        else:
            bash_params.extend(image_params)
        return self.docker_run_entrypoint(entrypoint=bash_binary, image_params=bash_params, options=options)

    def docker_run_entrypoint(self, entrypoint, image_params, options=None):
        entrypoint_params = ['--entrypoint', entrypoint]
        if type(image_params) is str:
            entrypoint_params.append(image_params)
        else:
            entrypoint_params.extend(image_params)
        return self.docker_run(entrypoint_params, options=options)

    @catch
    def image_build(self, path, image_repository, image_tag='latest'):
        image_name = f"{image_repository}:{image_tag}"
        (image,build_logs) = self.client().images.build(path=path, tag=image_name)
        return {'status': 'ok', 'image': image, 'build_logs': build_logs }

    def image_delete(self, image_name):
        return self.client().images.remove(image=image_name)

    def image_pull(self, repository, tag):
        return self.client().images.pull(repository, tag)

    def images(self):
        return self.client().images.list()

    def images_names(self):
        names = []
        for image in self.images():
            for tag in image.tags:
                names.append(tag)
        return sorted(names)

    def print_docker_comamnd(self, docker_params):
        if self.debug:
            print('******** Docker Command *******')
            print()
            print('docker', ' '.join(docker_params))
            print()
            print('******** Docker Command *******')
        return self

    def set_debug(self, value=True):
        self.debug = value
        return self

    def server_info(self):
        return self.client().info()

    def set_docker_run_timeout(self, value):
        self.docker_run_timeout = value
