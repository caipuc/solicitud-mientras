from .forms import ActivityFrom
from django.views import generic
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.mixins import LoginRequiredMixin


# LoginRequiredMixin acts as a decorator to make a login required
# for certain pages
class NewActivity(LoginRequiredMixin, generic.CreateView):
    def get(self, request):
        template = loader.get_template('new_activity.html')
        form = ActivityFrom(request.user)
        return HttpResponse(template.render({'form': form}, request))

    form_class = ActivityFrom
    success_url = reverse_lazy('home')
    template_name = 'new_activity.html'