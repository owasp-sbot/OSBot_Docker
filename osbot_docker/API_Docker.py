import docker
from osbot_utils.decorators.methods.cache_on_self import cache_on_self

from osbot_utils.decorators.methods.catch import catch

from osbot_utils.utils.Misc import trim, bytes_to_str, lower


class API_Docker:

    def __init__(self):
        pass

    @cache_on_self
    def client(self):
        return docker.from_env()

    @catch
    def container_run(self, repository, tag=None, command=None):
        if tag:
            image = f"{repository}:{tag}"
        else:
            image = repository

        output = self.client().containers.run(image, command)
        return { 'status': 'ok'   , 'output' : trim(bytes_to_str(output)) }

    def containers(self):
        return self.client().containers.list()

    @catch
    def image_build(self, path, tag):
        (image,build_logs) = self.client().images.build(path=path, tag=tag)
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