from pyramid.security import Allow


def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('add_loan', '/loans', factory=LoanResource)
    config.add_route('add_payment', '/loans/{loan_id}/payments',
                     factory=LoanResource)


class LoanResource(object):
    def __init__(self, request):
        self.request = request

    def __acl__(self):
        return [(Allow, 'API', 'edit'), (Allow, 'API', 'view')]
