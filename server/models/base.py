from sqlalchemy import orm

from server.utils.patch import patch_object


class Base(orm.DeclarativeBase):
    """
    Base class for all of our model classes, each of which corresponds to a
    database table.
    """
    __allow_update__ = []

    def has(self, attr):
        """
        Check if an attribute is loaded, especially useful for sqlalchemy lazy loading.
        """
        return attr in self.__dict__

    def update(self, data):
        """
        Update object with values from a dictionary.

        The update will only apply to attributes which are already defined
        and are present in the __allow_update__ class variable.
        """
        patch_object(self, data, allowed=self.__allow_update__)
