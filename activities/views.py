import json
from typing import ClassVar

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.html import strip_tags
from django.views import generic
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from accounts.models import Profile
from activities.forms import ActivityForm, NotificationForm
from activities.models import Activity, Space

from .models import Coordinator

DEBUG = settings.DEBUG
ACTIVITIES_PER_PAGE = 20


# Limits the permissions of viewing and modifying any of the activities that
# the user is not the owner and that the user dos not have permission to view
class PermissionMixin:
    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        # staff check
        if self.request.user.is_staff:
            return obj
        elif not obj.creator.id == self.request.user.id:
            raise PermissionDenied()
        else:
            return obj


# forces the user to fill the information of their profile
class FillInformation:
    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        if profile.rut == "" or profile.phone == "" or profile.profile_type == "":
            return redirect("update_profile", pk=user.id)
        else:
            return super().dispatch(request, *args, **kwargs)


class NewActivity(LoginRequiredMixin, FillInformation, PermissionMixin, generic.CreateView):
    form_class = ActivityForm
    model = Activity
    page_name = "new"
    template_name = "activities/activity_form.html"
    success_url = reverse_lazy("activities_list")

    def get(self, request, *args, **kwargs):
        template = loader.get_template("activities/activity_form.html")
        form = ActivityForm(request.user)
        required_links = list(Space.objects.filter(admin_required=True))
        return HttpResponse(
            template.render(
                {
                    "form": form,
                    "required_links": required_links,
                    "page_name": "Nueva actividad",
                    "button": "Crear actividad",
                },
                request,
            )
        )


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["required_links"] = list(Space.objects.filter(admin_required=True))
        context["page_name"] = "Nueva actividad"
        context["button"] = "Crear actividad"
        return context


class ActivitiesList(LoginRequiredMixin, FillInformation, generic.ListView):
    template_name = "activities/activities_list.html"
    model = Activity
    context_object_name = "activities"
    paginate_by = ACTIVITIES_PER_PAGE

    def get_queryset(self):
        maker = Q(creator=self.request.user)
        parameter = self.request.GET.get("search")

        if parameter != "" and parameter is not None:
            # searhch is by id
            if str.isnumeric(parameter):
                search = Q(id=int(parameter))

            # search is by name
            if str.isalpha(parameter):
                search = Q(name__icontains=parameter)

            return Activity.objects.filter(search & maker).order_by("-id")

        else:
            return Activity.objects.filter(maker).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_name"] = "Mis solicitudes"
        return context


class ActivitiesListStaff(ActivitiesList):
    template_name = "activities/activities_list_staff.html"

    def get_queryset(self):
        state = Q(state="PC") | Q(state="PA")
        parameter = self.request.GET.get("search")

        if parameter != "" and parameter is not None:
            # searhch is by id
            if str.isnumeric(parameter):
                search = Q(id=int(parameter))

            # search is by name
            if str.isalpha(parameter):
                search = Q(name__icontains=parameter)

            return Activity.objects.filter(search & state).order_by("-id")

        else:
            return Activity.objects.filter(state).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["url_search"] = "pending"
        context["page_name"] = "Solicitudes pendientes"
        return context


class ActivitiesListStaffAll(ActivitiesListStaff):
    def get_queryset(self):
        parameter = self.request.GET.get("search")

        if parameter != "" and parameter is not None:
            # searhch is by id
            if str.isnumeric(parameter):
                search = Q(id=int(parameter))

            # search is by name
            if str.isalpha(parameter):
                search = Q(name__icontains=parameter)

            return Activity.objects.filter(search).order_by("-id")

        else:
            return Activity.objects.all().order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["url_search"] = "all"
        context["page_name"] = "Todas las solicitudes"
        return context


class ActivityDelete(LoginRequiredMixin, FillInformation, PermissionMixin, generic.DeleteView):
    model = Activity
    template_name = "activities/activity_confirm_delete.html"
    success_url = reverse_lazy("activities_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["creator"] = Profile.objects.get(user=self.get_object().creator)
        context["page_name"] = "Eliminar actividad"
        context["button"] = "Eliminar"
        return context


class ActivityUpdate(LoginRequiredMixin, FillInformation, PermissionMixin, generic.UpdateView):
    model = Activity
    form_class = ActivityForm
    page_name = "updates"
    template_name = "activities/activity_form.html"
    success_url = reverse_lazy("activities_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["creator"] = Profile.objects.get(user=self.get_object().creator)
        context["required_links"] = list(Space.objects.filter(admin_required=True))
        context["page_name"] = "Actualizar actividad"
        context["button"] = "Actualizar actividad"
        return context


class ActivityDetail(LoginRequiredMixin, FillInformation, PermissionMixin, generic.DetailView):
    model = Activity
    template_name = "activities/detailed_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["creator"] = Profile.objects.get(user=self.get_object().creator)
        context["page_name"] = "Detalle de la actividad"
        return context


class ActivityChangeState(LoginRequiredMixin, FillInformation, PermissionMixin, generic.UpdateView):
    model = Activity
    success_url = reverse_lazy("activities_list")
    fields: ClassVar[list[str]] = ["state"]
    page_name = "Cambio de estado de solicitud"
    template_name = "activities/activities_status_update_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["creator"] = Profile.objects.get(user=self.get_object().creator)
        context["required_links"] = list(Space.objects.filter(admin_required=True))
        context["page_name"] = "Cambio de estado solicitud"
        context["button"] = "Cambiar estado de actividad"
        return context



class ActivityStatusNotification(LoginRequiredMixin, FillInformation, PermissionMixin, generic.FormView):
    form_class = NotificationForm
    model = Activity
    page_name = "Notificar cambio de estado"
    template_name = "activities/notify_status_change.html"

    def form_valid(self, form):
        activity = Activity.objects.get(pk=self.kwargs["pk"])
        
        # Aquí puedes personalizar el contenido del correo según tu necesidad
        subject = form.cleaned_data["subject"]
        body = form.cleaned_data["body"]
        
        # Aquí envías el correo electrónico
        self.send_notification_email(subject, body, "olguita.barriga@caiuc.cl", [activity.in_charge])

        messages.info(self.request, f"Se ha enviado un correo a {activity.in_charge}")
        return redirect("activities_list_staff")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_name"] = "Notificar cambio de estado"
        context["button"] = "Enviar correo"
        return context

    def send_notification_email(self, subject, body, from_email, recipient_list):
        # Aquí puedes utilizar la lógica de envío de correos electrónicos
        # Puedes usar la función send_mail o cualquier método que prefieras
        # Asegúrate de configurar adecuadamente las configuraciones de correo en tu settings.py

        from django.core.mail import send_mail

        send_mail(subject, body, from_email, recipient_list)


class Calendar(generic.TemplateView):
    page_name = "calendar"
    template_name = "activities/calendar.html"

    def get(self, request):
        template = loader.get_template("activities/calendar.html")
        events = []
        for activity in Activity.objects.filter(state="A"):
            events.extend(activity.activity_format_calendar)
        spaces = []
        for space in Space.objects.all():
            spaces.append(space)
        return HttpResponse(
            template.render(
                {
                    "events": json.dumps(events),
                    "spaces": spaces,
                    "page_name": "Calendario de actividades",
                },
                request,
            )
        )


class HomeWithCalendar(LoginRequiredMixin, FillInformation, generic.TemplateView):
    page_name = "home"
    template_name = "home.html"

    def get(self, request):
        template = loader.get_template("home.html")
        events = []
        for activity in Activity.objects.filter(state="A", creator=request.user):
            events.extend(activity.activity_format_calendar)
        spaces = []
        for space in Space.objects.all():
            spaces.append(space)
        return HttpResponse(template.render({"events": json.dumps(events), "spaces": spaces}, request))
# Función para enviar el correo de confirmación
def enviar_correo_confirmacion(sender, instance, created, **kwargs):
    if created:
        # Aquí defines el contenido del correo
        subject = 'Nueva actividad creada'
        message = f'Se ha creado una nueva actividad: {instance}'
        from_email = 'tu_email@gmail.com'  # Coloca tu dirección de correo
        recipient_list = ['olguita.barriga@caiuc.cl']  # Lista de destinatarios
        send_mail(subject, message, from_email, recipient_list)

# Registra la señal para la función enviar_correo_confirmacion
post_save.connect(enviar_correo_confirmacion, sender=NewActivity)
