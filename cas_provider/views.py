from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login, logout as auth_logout

from forms import LoginForm
from models import ServiceTicket, LoginTicket
from utils import create_service_ticket

__all__ = ['login', 'validate', 'logout']

def login(request, template_name='cas/login.html', success_redirect='/accounts/'):
    service = request.GET.get('service', None)
    if request.user.is_authenticated():
        if service is not None:
            ticket = create_service_ticket(request.user, service)
            if service.find('?') == -1:
                return HttpResponseRedirect(service + '?ticket=' + ticket.ticket)
            else:
                return HttpResponseRedirect(service + '&ticket=' + ticket.ticket)
        else:
            return HttpResponseRedirect(success_redirect)
    errors = []
    if request.method == 'POST':
        email = request.POST.get('email', None)
        password = request.POST.get('password', None)
        service = request.POST.get('service', None)
        lt = request.POST.get('lt', None)
        if not request.POST.get('remember_me', None):
          request.session.set_expiry(0)
                
        try:
            login_ticket = LoginTicket.objects.get(ticket=lt)
        except:
            errors.append('Login ticket expired. Please try again.')
        else:
            login_ticket.delete()
            user = authenticate(username=email, password=password)
            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    if service is not None:
                        ticket = create_service_ticket(user, service)
                        return HttpResponseRedirect(service + '?ticket=' + ticket.ticket)
                    else:
                        return HttpResponseRedirect(success_redirect)
                else:
                    errors.append('This account is disabled.')
            else:
                    errors.append('Incorrect username and/or password.')
    form = LoginForm(service)
    return render_to_response(template_name, {'form': form, 'errors': errors}, context_instance=RequestContext(request))
    
def validate(request):
    service = request.GET.get('service', None)
    ticket_string = request.GET.get('ticket', None)
    if service is not None and ticket_string is not None:
        try:
            ticket = ServiceTicket.objects.get(ticket=ticket_string)
            ### NOTE: We've changed this to return the email address, not the username.
            email = ticket.user.email
            ticket.delete()
            return HttpResponse("yes\n%s\n" % email)
        except:
            pass
    return HttpResponse("no\n\n")
    
def logout(request, template_name='cas/logout.html'):
    url = request.GET.get('url', None)
    auth_logout(request)
    return render_to_response(template_name, {'url': url}, context_instance=RequestContext(request))
