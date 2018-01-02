from pyramid.view import forbidden_view_config, notfound_view_config


@notfound_view_config(renderer='json')
def notfound_view(request):
    request.response.status = 404
    return {}


@forbidden_view_config(renderer='json')
def forbidden_view(request):
    request.response.status = 403
    return {}
