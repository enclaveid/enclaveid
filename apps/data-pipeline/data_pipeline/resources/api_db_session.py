from dagster import ConfigurableResource, InitResourceContext
from pydantic import PrivateAttr
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session


class ApiDbSession(ConfigurableResource):
    _engine: Engine = PrivateAttr()
    _session: Session = PrivateAttr()
    _classes = PrivateAttr()

    conn_string: str

    def setup_for_execution(self, context: InitResourceContext):
        self._engine = create_engine(self.conn_string)
        Base = automap_base()
        Base.prepare(self._engine, reflect=True)
        self._classes = Base.classes
        self._session = Session(self._engine)

    def get_mapped_class(self, table_name):
        return getattr(self._classes, table_name)

    def get_session(self):
        return self._session
