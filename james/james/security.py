import hashlib

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy


class AuthenticationPolicy(AuthTktAuthenticationPolicy):
    def unauthenticated_userid(self, request):
        if request.headers.get('authorization') == hashlib.sha256(request.registry.settings.get('api.key', '')).hexdigest():
            return 'API'

        return super(AuthenticationPolicy, self).unauthenticated_userid(request)


def includeme(config):
    settings = config.get_settings()
    authn_policy = AuthenticationPolicy(
        settings['auth.secret'],
        hashalg='sha512',
    )
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(ACLAuthorizationPolicy())
