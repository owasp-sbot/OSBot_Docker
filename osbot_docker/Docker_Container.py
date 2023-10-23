from docker.errors                       import NotFound

from osbot_docker.API_Docker                import API_Docker
from osbot_utils.decorators.methods.catch   import catch
from osbot_utils.utils.Misc                 import date_time_from_to_str, wait_for, trim, bytes_to_str


class Docker_Container:

    def __init__(self, container_id, api_docker:API_Docker=None):
        self.api_docker   = api_docker or API_Docker()
        self.container_id = container_id

    def __repr__(self):
        return f"<Docker_Container: {self.short_id()}>"

    def client_api(self):
        return self.api_docker.client_api()

    def client_docker(self):
        return self.api_docker.client_docker()

    def delete(self):
        if self.exists():
            if self.status() != 'running':
                self.client_api().remove_container(self.container_id)
                return True
        return False

    def image(self):
        return self.info().get('image')

    def info(self):
        container_raw = self.info_raw()
        return self.info_raw_parse(container_raw)

    def info_raw(self):
        try:
            container = self.client_docker().containers.get(self.container_id)
            return container.attrs
        except NotFound:
            return {}


    def info_raw_parse(self, container_raw):
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

    def exists(self):
        return self.info_raw() != {}

    def exec(self, command, workdir=None):
        """Executes a command inside a running Docker container."""
        exec_instance   = self.client_api().exec_create(self.container_id, cmd=command, workdir=workdir)
        result          = self.client_api().exec_start(exec_instance['Id'])
        return result.decode('utf-8')

    def labels(self):
        return self.info().get('labels') or {}

    def logs(self):
        if self.exists():
            logs = self.client_api().logs(self.container_id)
            if logs:
                return logs.decode('utf-8')
        return ''

    def start(self, wait_for_running=True):
        self.client_api().start(container=self.container_id)
        if wait_for_running:
            return self.wait_for_container_status('running')
        return True

    def short_id(self):
        return self.container_id[:12]

    def stop(self, wait_for_exit=True):
        if self.status() != 'running':
            return False
        self.client_api().stop(container=self.container_id)
        if wait_for_exit:
            self.wait_for_container_status('exited')
        return True

    def status(self):
        return self.info().get('status') or 'not found'

    def wait_for_container_status(self, desired_status, wait_delta=.2, wait_count=10):
        while wait_count > 0:
            container_status = self.status()
            print(f'{wait_count}: {self.container_id} : {container_status}')
            if container_status is None:
                return False
            if container_status == desired_status:
                return True                                 # Container has reached the desired status
            wait_for(wait_delta)
            wait_count-=1
        return False