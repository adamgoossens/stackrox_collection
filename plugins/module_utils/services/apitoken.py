from ansible_collections.community.stackrox.plugins.module_utils.basic import StackroxService
from ansible_collections.community.stackrox.plugins.module_utils import exceptions

class Service(StackroxService):
    def __init__(self, **kwargs):
        kwargs['api_base'] = 'apitokens'
        super().__init__(**kwargs)

    def list(self, include_revoked=False):
        """
        Return a list of all API tokens.

        By default this will exclude all tokens that have been revoked.

        To include these, set `include_revoked` to `True`.
        """

        res = self._request(
                query_string=f"revoked={str(include_revoked).lower()}"
              )

        return res['tokens']

    def get(self, name=None, id=None, include_revoked=False):
        """
        Return an API token by either name or ID.

        If ID is provided, this will be used by preference if Name is also provided.

        If only Name is provided, then all tokens will be fetched to find
        the match. You may end up with multiple tokens returned as names are not unique
        within the Stackrox API.
        """
        
        if not name and not id:
            raise Exception("Either name or id must be provided")

        matched_tokens = []

        def include_token(t):
            return ((not t['revoked']) or (t['revoked'] and include_revoked))

        if id:
            t = self._request(
                        url_suffix=id
                    )

            # token is either not revoked,
            # or is revoked and we're including it anyway
            if include_token(t):
                matched_tokens.append(t)

        else:
            matched_tokens = [ t for t in self.list(include_revoked) if t['name'] == name and include_token(t) ]

        return matched_tokens

    def create(self, name, role):
        """
        Create a token with the given name and assign the provided role.

        Names are not unique within Stackrox; there can be several tokens with the same name.

        Roles are strings and correspond to the role names as found in the API, e.g. "Continous Integration".
        """

        token = self._request(
                    url_suffix='generate',
                    method='POST',
                    data={"name": name, "role": role}
                )

        return token

    def revoke(self, id=None, name=None):
        """
        Revoke the token with the given ID or Name.

        Revoking by name will only work if the token name is unique (remember again
        that token names are not enforced unique in the Stackrox API). If there are multiple
        tokens that match the name, this method will fail.

        To be sure, revoke by ID only.
        """

        if not id and not name:
            raise Exception("Either token ID or name must be provided.")

        if not id and name:
            # no ID provided but we have a name

            # fetch the token and get the ID
            token = self.get(name=name)

            if isinstance(token, list):
                raise Exception(f"More than one active token with the name {name} was found. Use token ID instead.")

            id = token['id']

        result = self._request(method="PATCH",
                                url_suffix=f"revoke/{id}")

        return True
