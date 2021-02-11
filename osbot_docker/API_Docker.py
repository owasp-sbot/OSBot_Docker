import docker
from osbot_utils.decorators.lists.group_by import group_by
from osbot_utils.decorators.lists.index_by import index_by
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
    def container_run(self, repository, tag='latest', command=None):
        if tag:
            image = self.image_name(repository, tag)
        else:
            image = repository

        output = self.client().containers.run(image, command)
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

    def docker_run(self, image_params, options=None):
        """Use this method to invoke the docker executable directly
            image_params is an image name of an array of image name + image params"""

        if image_params:
            if type(image_params) is str:
                image_params = [image_params]

        docker_params = ['run', '--rm']
        self.docker_params_append_options(docker_params=docker_params, options=options)
        docker_params.extend(image_params)
        self.print_docker_command(docker_params)                # todo: refactor to use logging class

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

    def format_image(self, target):
        data = target.attrs
        data['Labels' ] = target.labels
        data['ShortId'] = target.short_id
        data['Tags'   ] = target.tags
        return data

    @catch
    def image_build(self, path, repository, tag='latest'):
        image_name = self.image_name(repository, tag)
        (result,build_logs) = self.client().images.build(path=path, tag=image_name)
        return {'status': 'ok', 'image': result.attrs, 'tags':result.tags, 'build_logs': build_logs }

    def image_delete(self, repository, tag='latest'):
        if self.image_exists(repository, tag):
            image_name = self.image_name(repository, tag)
            self.client().images.remove(image=image_name)
            return self.image_exists(repository, tag) is False
        return False

    def image_info(self, repository, tag='latest'):
        try:
            image_name = self.image_name(repository,tag)
            result     = self.client().images.get(image_name)
            return self.format_image(result)
        except Exception as error:
            return None

    def image_exists(self, repository, tag='latest'):
        return self.image_info(repository, tag) is not None

    def image_name(self, repository, tag):
        return f"{repository}:{tag}"

    def image_pull(self, repository, tag):
        return self.client().images.pull(repository, tag)

    def image_push(self, repository, tag):
        return self.client().images.push(repository, tag)

    @index_by
    @group_by
    def images(self):
        images = []
        for image in self.client().images.list():
            images.append(self.format_image(image))
        return images

    def images_names(self):
        names = []
        for image in self.images():
            for tag in image.get('Tags'):
                names.append(tag)
        return sorted(names)

    def print_docker_command(self, docker_params):
        if self.debug:
            print('******** Docker Command *******')
            print()
            print('docker', ' '.join(docker_params))
            print()
            print('******** Docker Command *******')
        return self

    def registry_login(self, registry, username, password):
        return self.client().login(username=username, password=password, registry=registry)

    def set_debug(self, value=True):
        self.debug = value
        return self

    def server_info(self):
        return self.client().info()

    def set_docker_run_timeout(self, value):
        self.docker_run_timeout = value
