def run(event, context=None):
    name = event.get('name') or 'world'
    return f'docker - hello {name}!'