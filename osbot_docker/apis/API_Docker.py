from collections import defaultdict

import docker
from docker                                         import APIClient

from osbot_utils.utils.Misc import bytes_to_str

from osbot_utils.decorators.lists.group_by          import group_by
from osbot_utils.decorators.lists.index_by          import index_by
from osbot_utils.utils.Process                      import exec_process
from osbot_utils.decorators.methods.cache_on_self   import cache_on_self
from osbot_utils.decorators.methods.catch           import catch
from osbot_utils.utils.Str import trim


class API_Docker:

    def __init__(self, debug=False):
        self.debug              = debug
        self.docker_run_timeout = None

    @cache_on_self
    def client_api(self):
        return APIClient(version='auto')

    def client_api_version(self):
        return self.client_api_version_raw().get('ApiVersion')

    def client_api_version_raw(self):
        return self.client_api().version()

    @cache_on_self
    def client_docker(self):
        return docker.from_env()

    def client_docker_version_raw(self):
        return self.client_docker().version()

    def container(self, container_id):
        from osbot_docker.apis.Docker_Container import Docker_Container
        return Docker_Container(container_id=container_id, api_docker=self)

    def container_create(self, image_name, command='', tag='latest', volumes=None, tty=False, port_bindings=None, labels=None):
        from osbot_docker.apis.Docker_Image import Docker_Image
        image = Docker_Image(image_name=image_name, image_tag=tag, api_docker=self)
        return image.create_container(command=command, volumes=volumes, tty=tty, port_bindings=port_bindings, labels=labels)


    @catch
    def container_run(self, image_name, tag='latest', command=None, auto_remove=False, detach=False,
                      tty=False):  # todo: figure out why auto_remove throws an exception

        from osbot_docker.apis.Docker_Image import Docker_Image
        image = Docker_Image(image_name=image_name, image_tag=tag, api_docker=self).image_name_with_tag()

        output = self.client_docker().containers.run(image, command, auto_remove=auto_remove, detach=detach, tty=tty)
        return {'status': 'ok', 'output': trim(bytes_to_str(output))}

    @index_by
    @group_by
    def containers(self, **kwargs):
        from osbot_docker.apis.Docker_Container import Docker_Container      # note: we have to import here due to circular dependency
        containers = []
        for container_raw in self.containers_raw(**kwargs):
            container_id = container_raw.id
            docker_container = Docker_Container(container_id=container_id, api_docker=self, container_raw=container_raw)
            #container = self.container_attrs_parse(container_raw.attrs)
            containers.append(docker_container)
        return containers

    @index_by
    @group_by
    def containers_all(self, **kwargs):
        return self.containers(all=True, **kwargs)

    def containers_all__by_id(self):
        containers_by_id = {}
        for container in self.containers_all():
            containers_by_id[container.short_id()] = container
        return containers_by_id

    def containers_all__by_labels(self):
        containers_by_labels = defaultdict(lambda: defaultdict(dict))
        for container in self.containers_all():
            labels = container.container_raw.labels or {}
            for label_id, label_value in labels.items():
                containers_by_labels[label_id][label_value][container.short_id()] = container
        return containers_by_labels

    def containers_all__with_image(self, image_name, tag='latest'):
        from osbot_docker.apis.Docker_Image import Docker_Image
        image = Docker_Image(image_name=image_name, image_tag=tag, api_docker=self).image_name_with_tag()
        containers_with_image = []
        for container in self.containers_all():
            if image in container.image():
                containers_with_image.append(container)
        return containers_with_image

    def containers_raw(self, all=True, filters=None, since=None, before=None, limit=None, sparse  = False):
        kwargs = dict(all     = all     ,
                      filters = filters ,
                      since   = since   ,
                      before  = before  ,
                      limit   = limit   ,
                      sparse  = sparse  )           # set to True when we mainly want to container id
        return self.client_docker().containers.list(**kwargs)

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


    @index_by
    @group_by
    def images(self):
        from osbot_docker.apis.Docker_Image import Docker_Image     # note: we have to import here due to circular dependency
        images = []
        for image_data in self.client_api().images():
            for tag in image_data.get('RepoTags') or []:
                if tag != '<none>:<none>':
                    image_name, tag = tag.split(':')
                    image_id        = image_data.get('Id').split(':')[1]
                    image = Docker_Image(image_id = image_id, image_name=image_name, image_tag=tag)
                    images.append(image)
        #for image in self.client_docker().images.list():
        #    images.append(self.format_image(image))
        return images

    def images_names(self):
        names = []
        for image in self.images():
            names.append(image.name())
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
        return self.client_docker().login(username=username, password=password, registry=registry)

    def set_debug(self, value=True):
        self.debug = value
        return self

    def server_info(self):
        return self.client_docker().info()

    def set_docker_run_timeout(self, value):
        self.docker_run_timeout = value
