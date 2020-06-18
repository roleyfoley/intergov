from intergov.loggers import logging

from intergov.monitoring import statsd_timer


class AuthenticatedObjectAccessUseCase:
    """
    Used by the document/object retrieve API

    Receive ACL and object lake repos
    Receive URI which is a multihash of the file
    Receive auth_country - a country which is trying to access this object
    Returns obj body or None or raises an Exception
    Checks if this country can access this object and returns it if exists
    """

    def __init__(self, object_acl_repo, object_lake_repo):
        self.object_acl = object_acl_repo
        self.object_lake = object_lake_repo

    @statsd_timer("usecase.AuthenticatedObjectAccessUseCase.execute")
    def execute(self, uri, auth_country):
        authenticated_countries = self.object_acl.search({'object__eq': uri})
        if auth_country not in authenticated_countries:
            # it's not much of an error, just useful for debug to see what's wrong
            logging.error("Actor %s tried to access %s but can't", auth_country, uri)
            return None
        try:
            obj = self.object_lake.get_body(uri)
        except Exception as e:
            if e.__class__.__name__ == 'NoSuchKey':
                obj = None
            else:
                raise e

        if not obj:
            logging.error(
                "For object %s the ACL record exists but object lake one is not",
                uri
            )
            return None
        else:
            return obj
