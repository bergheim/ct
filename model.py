import ConfigParser
from elixir import *
from model import *

class User(Entity):
    username = Field(Unicode(20), unique=True)
    password = Field(Unicode(30))

    def __repr__(self):
        return "<User %d: %s/%s>" % (self.id, self.username, self.password)

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read(["config.ini.sample", "config.ini"])

    metadata.bind = config.get("server", "db")
    metadata.bind.echo = True

    setup_all()
    create_all()


