import docker
from docker                                         import APIClient
from osbot_utils.utils.Misc import trim, bytes_to_str

from osbot_utils.decorators.lists.group_by          import group_by
from osbot_utils.decorators.lists.index_by          import index_by
from osbot_utils.utils.Process                      import exec_process
from osbot_utils.decorators.methods.cache_on_self   import cache_on_self
from osbot_utils.decorators.methods.catch           import catch

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
        from osbot_docker.Docker_Container import Docker_Container
        return Docker_Container(container_id=container_id, api_docker=self)

    def container_create(self, image_name, command='', tag='latest', volumes=None, tty=False):
        """Creates a Docker container and returns its ID."""
        if tag:
            image = self.image_name_with_tag(image_name, tag)
        else:
            image = image_name

        host_config  = self.client_api().create_host_config(binds=volumes)
        container    = self.client_api().create_container  (image=image, command=command, host_config=host_config, tty=tty)
        container_id = container.get('Id')
        from osbot_docker.Docker_Container import Docker_Container                  # note: we have to import here due to circular dependency
        return Docker_Container(container_id=container_id, api_docker=self)

    @catch
    def container_run(self, image_name, tag='latest', command=None, auto_remove=False, detach=False,
                      tty=False):  # todo: figure out why auto_remove throws an exception
        if tag:
            image = self.image_name_with_tag(image_name, tag)
        else:
            image = image_name

        output = self.client_docker().containers.run(image, command, auto_remove=auto_remove, detach=detach, tty=tty)
        return {'status': 'ok', 'output': trim(bytes_to_str(output))}

    @index_by
    @group_by
    def containers(self, **kwargs):
        from osbot_docker.Docker_Container import Docker_Container      # note: we have to import here due to circular dependency
        containers = []
        for container_raw in self.containers_raw(**kwargs):
            container_id = container_raw.id
            docker_container = Docker_Container(container_id=container_id, api_docker=self)
            #container = self.container_attrs_parse(container_raw.attrs)
            containers.append(docker_container)
        return containers

    @index_by
    @group_by
    def containers_all(self, **kwargs):
        return self.containers(all=True, **kwargs)

    def containers_all__indexed_by_id(self):
        containers_by_id = {}
        for container in self.containers_all():
            containers_by_id[container.short_id()] = container
        return containers_by_id

    def containers_all__with_image(self, image_name, tag='latest'):
        image = self.image_name_with_tag(image_name, tag)
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

    def format_image(self, target):
        data = target.attrs
        data['Labels' ] = target.labels
        data['ShortId'] = target.short_id
        data['Tags'   ] = target.tags
        return data

    @catch
    def image_build(self, path, image_name, tag='latest'):
        image_name = self.image_name_with_tag(image_name, tag)
        (result,build_logs) = self.client_docker().images.build(path=path, tag=image_name)
        return {'status': 'ok', 'image': result.attrs, 'tags':result.tags, 'build_logs': build_logs }

    def image_delete(self, image_name, tag='latest'):
        if self.image_exists(image_name, tag):
            image = self.image_name_with_tag(image_name, tag)
            self.client_docker().images.remove(image=image)
            return self.image_exists(image_name, tag) is False
        return False

    def image_info(self, image_name, tag='latest'):
        try:
            image  = self.image_name_with_tag(image_name, tag)
            result = self.client_docker().images.get(image)
            return self.format_image(result)
        except Exception as error:
            return None

    def image_exists(self, image_name, tag='latest'):
        return self.image_info(image_name, tag) is not None

    def image_name_with_tag(self, image_name, tag):
        return f"{image_name}:{tag}"

    def image_pull(self, image_name, tag):
        return self.client_docker().images.pull(image_name, tag)

    def image_push(self, image_name, tag):
        return self.client_docker().images.push(image_name, tag)

    @index_by
    @group_by
    def images(self):
        images = []
        for image in self.client_docker().images.list():
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
        return self.client_docker().login(username=username, password=password, registry=registry)

    def set_debug(self, value=True):
        self.debug = value
        return self

    def server_info(self):
        return self.client_docker().info()

    def set_docker_run_timeout(self, value):
        self.docker_run_timeout = value
