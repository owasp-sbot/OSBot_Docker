from datetime import datetime

import docker
from docker                                         import APIClient
from docker.errors import NotFound

from osbot_utils.decorators.lists.group_by          import group_by
from osbot_utils.decorators.lists.index_by          import index_by
from osbot_utils.utils.Process                      import exec_process
from osbot_utils.decorators.methods.cache_on_self   import cache_on_self
from osbot_utils.decorators.methods.catch           import catch
from osbot_utils.utils.Misc import trim, bytes_to_str, obj_info, date_time_now, date_time_from_to_str, wait_for


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
        container_raw = self.container_raw(container_id)
        return self.container_attrs_parse(container_raw)

    def container_attrs_parse(self, container_raw):
        if container_raw == {}:
            return {}
        config      = container_raw.get('Config'         )
        created_raw = container_raw.get('Created'        )[:26] + 'Z'       # need to remove the micro seconds
        created     = date_time_from_to_str(created_raw, '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d %H:%M', True)
        network     = container_raw.get('NetworkSettings')
        state       = container_raw.get('State'          )

        return dict(args        = container_raw.get('Args'         ),
                    created     = created                           ,
                    entrypoint  = config       .get('Entrypoint'   ),
                    env         = config       .get('Env'          ),
                    id          = container_raw.get('Id'           ),
                    id_short    = container_raw.get('Id'      )[:12],
                    image       = config       .get('Image'        ),
                    labels      = config       .get('Labels'       ),
                    name        = container_raw.get('Name'         ),
                    ports       = network      .get('Ports'        ),
                    status      = state        .get('Status'       ),
                    volumes     = config       .get('Volumes'      ),
                    working_dir = config       .get('WorkingDir'   ))




    def container_create(self, image_name, command='', tag='latest', volumes=None, tty=False):

        """Creates a Docker container and returns its ID."""
        if tag:
            image = self.image_name_with_tag(image_name, tag)
        else:
            image = image_name

        host_config = self.client_api().create_host_config(binds=volumes)
        container   = self.client_api().create_container  (image=image, command=command, host_config=host_config, tty=tty)
        return container.get('Id')

    def container_delete(self, container_id):
        if self.container_exists(container_id):
            if self.container_status(container_id) != 'running':
                self.client_api().remove_container(container_id)
                return True
        return False

    def container_exists(self, container_id):
        return self.container_raw(container_id) != {}

    def container_exec(self, container_id, command, workdir=None):
        """Executes a command inside a running Docker container."""
        exec_instance   = self.client_api().exec_create(container_id, cmd=command, workdir=workdir)
        result          = self.client_api().exec_start(exec_instance['Id'])
        return result.decode('utf-8')

    def container_logs(self, container_id):
        if self.container_exists(container_id):
            logs = self.client_api().logs(container_id)
            if logs:
                return logs.decode('utf-8')
        return ''

    def container_start(self, container_id, wait_for_running=True):
        self.client_api().start(container=container_id)
        if wait_for_running:
            return self.wait_for_container_status(container_id, 'running')
        return True

    def container_stop(self, container_id, wait_for_exit=True):
        if self.container_status(container_id) != 'running':
            return False
        self.client_api().stop(container=container_id)
        if wait_for_exit:
            self.wait_for_container_status(container_id, 'exited')
        return True

    def container_status(self, container_id):
        return self.container(container_id).get('status') or 'not found'

    def container_raw(self, container_id):
        try:
            container = self.client_docker().containers.get(container_id)
            return container.attrs
        except NotFound:
            return {}


    @catch
    def container_run(self, image_name, tag='latest', command=None, auto_remove=False, detach=False, tty=False):   # todo: figure out why auto_remove throws an exception
        if tag:
            image = self.image_name_with_tag(image_name, tag)
        else:
            image = image_name

        output = self.client_docker().containers.run(image, command, auto_remove=auto_remove, detach=detach, tty=tty)
        return { 'status': 'ok'   , 'output' : trim(bytes_to_str(output)) }

    @index_by
    @group_by
    def containers(self, **kwargs):
        containers = []
        for container_raw in self.containers_raw(**kwargs):
            container = self.container_attrs_parse(container_raw.attrs)
            containers.append(container)
        return containers

    @index_by
    @group_by
    def containers_all(self, **kwargs):
        return self.containers(all=True, **kwargs)

    def containers_all__indexed_by_id(self):
        return self.containers(index_by='id_short')

    def containers_all__with_image(self, image_name, tag='latest'):
        image = self.image_name_with_tag(image_name, tag)
        return self.containers_all(group_by='image').get(image,[])

    def containers_raw(self, all=True, filters=None, since=None, before=None, limit=None):
        kwargs = dict(all     = all     ,
                      filters = filters ,
                      since   = since   ,
                      before  = before  ,
                      limit   = limit   )
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

    def wait_for_container_status(self, container_id, desired_status, wait_delta=.2, wait_count=10):
        while wait_count > 0:
            container_status = self.container_status(container_id)
            print(f'{wait_count}: {container_id} : {container_status}')
            if container_status is None:
                return False
            if container_status == desired_status:
                return True                                 # Container has reached the desired status
            wait_for(wait_delta)
            wait_count-=1
        return False