from charms.layer.hookenv import pod_spec_set
from charms.reactive import when, when_not
from charms.reactive.flags import set_flag, get_state
from charmhelpers.core.hookenv import log, metadata, status_set, config,\
     network_get, relation_id


@when_not('mysql.configured')
def config_gitlab():
    status_set('maintenance', 'Configuring mysql container')

    spec = make_pod_spec()
    log('set pod spec:\n{}'.format(spec))
    pod_spec_set(spec)

    set_flag('mysql.configured')
    status_set('maintenance', 'Creating mysql container')


def make_pod_spec():
    spec_file = open('reactive/spec_template.yaml')
    pod_spec_template = spec_file.read()

    md = metadata()
    cfg = config()

    user = cfg.get('user', 'test')
    set_flag('user', user)
    password = cfg.get('password', 'letmein')
    set_flag('password', password)
    database = cfg.get('database', 'juju')
    set_flag('database', database)
    root_password = cfg.get('root_password', 'admin')
    set_flag('root_password', root_password)

    data = {
        'name': md.get('name'),
        'image': cfg.get('mysql_image'),
        'port': cfg.get('mysql_port'),
        'user': user,
        'password': password,
        'database': database,
        'root_password': root_password,
    }
    data.update(cfg)
    return pod_spec_template % data


@when('server.database.requested')
def provide_database(mysql):
    log('db requested')

    for service in mysql.requested_databases():
        log('request for {0}'.format(service))
        database = get_state('database')
        user = get_state('user')
        password = get_state('password')

        log('db params: {0}:{1}@{2}'.format(user, password, database))
        info = network_get('server', relation_id())
        log('network info {0}'.format(info))

        mysql.provide_database(
            service=service,
            host=info['ingress-addresses'][0],
            port=3306,
            database=database,
            user=user,
            password=password,
        )
