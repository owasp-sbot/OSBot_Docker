import docker
from osbot_utils.utils.Process import exec_process

from osbot_utils.decorators.methods.cache_on_self import cache_on_self

from osbot_utils.decorators.methods.catch import catch

from osbot_utils.utils.Misc import trim, bytes_to_str


class API_Docker:

    def __init__(self):
        pass

    @cache_on_self
    def client(self):
        return docker.from_env()

    @catch
    def container_run(self, repository, tag='latest', command=None):
        if tag:
            image = f"{repository}:{tag}"
        else:
            image = repository

        output = self.client().containers.run(image, command)
        return { 'status': 'ok'   , 'output' : trim(bytes_to_str(output)) }

    def containers(self):
        return self.client().containers.list()

    def docker_run(self, image_params):
        """Use this method to invoke the docker executable directly
            image_params is an image name of an array of image name + image params"""

        if image_params:
            if type(image_params) is str:
                image_params = [image_params]

        docker_params = ['run', '--rm']
        docker_params.extend(image_params)

        return exec_process('docker', docker_params)

    def docker_run_bash(self, image_name, image_params, bash_binary='/bin/bash'):
        bash_params = [image_name, '-c']
        if type(image_params) is str:
            bash_params.append(image_params)
        else:
            bash_params.extend(image_params)
        return self.docker_run_entrypoint(bash_binary, bash_params)

    def docker_run_entrypoint(self, entrypoint, image_params):
        entrypoint_params = ['--entrypoint', entrypoint]
        if type(image_params) is str:
            entrypoint_params.append(image_params)
        else:
            entrypoint_params.extend(image_params)
        return self.docker_run(entrypoint_params)


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

    def server_info(self):
        return self.client().info()