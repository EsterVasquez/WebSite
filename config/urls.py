"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from app.api_views import (
    available_times_api,
    calendar_context_api,
    confirm_booking_api,
    dashboard_booking_status_api,
    dashboard_bookings_api,
    dashboard_bookings_events_api,
    dashboard_manual_available_times_api,
    dashboard_manual_booking_create_api,
    dashboard_services_api,
)
from app.bot_manager_views import (
    bot_manager,
    create_node,
    create_option,
    delete_node,
    delete_option,
    reorder_nodes,
    reorder_options,
    update_node,
    update_option,
)
from app.service_manager_views import (
    create_exception,
    create_package,
    create_service,
    create_weekly_range,
    delete_exception,
    delete_package,
    delete_service,
    delete_weekly_range,
    service_manager,
    update_exception,
    update_package,
    update_service,
    update_weekly_range,
)
from app.views import auth_login, calendar, calendar_view, manual_booking, user_calendar, webhook

urlpatterns = [
    path('', calendar, name='calendar'),
    path('admin/', admin.site.urls),
    path('webhook/', webhook, name='webhook'),
    path('calendario/<uuid:token>/', user_calendar, name='user_calendar'),
    path('login/', auth_login, name='login'),
    path('api/dashboard/bookings/', dashboard_bookings_api, name='dashboard_bookings_api'),
    path('api/dashboard/bookings/events/', dashboard_bookings_events_api, name='dashboard_bookings_events_api'),
    path('api/dashboard/bookings/<int:booking_id>/status/', dashboard_booking_status_api, name='dashboard_booking_status_api'),
    path('api/dashboard/services/', dashboard_services_api, name='dashboard_services_api'),
    path('api/dashboard/manual/available-times/', dashboard_manual_available_times_api, name='dashboard_manual_available_times_api'),
    path('api/dashboard/manual/bookings/create/', dashboard_manual_booking_create_api, name='dashboard_manual_booking_create_api'),
    path('api/calendar/<uuid:token>/context/', calendar_context_api, name='calendar_context_api'),
    path('api/calendar/<uuid:token>/available-times/', available_times_api, name='available_times_api'),
    path('api/calendar/<uuid:token>/confirm/', confirm_booking_api, name='confirm_booking_api'),
    path('calendario-panel/', calendar_view, name='calendar_view'),
    path('citas/nueva/', manual_booking, name='manual_booking'),
    path('bot-manager/', bot_manager, name='bot_manager'),
    path('bot-manager/node/create/', create_node, name='bot_manager_create_node'),
    path('bot-manager/node/<int:node_id>/update/', update_node, name='bot_manager_update_node'),
    path('bot-manager/node/<int:node_id>/delete/', delete_node, name='bot_manager_delete_node'),
    path('bot-manager/node/<int:node_id>/options/create/', create_option, name='bot_manager_create_option'),
    path('bot-manager/option/<int:option_id>/update/', update_option, name='bot_manager_update_option'),
    path('bot-manager/option/<int:option_id>/delete/', delete_option, name='bot_manager_delete_option'),
    path('bot-manager/reorder/nodes/', reorder_nodes, name='bot_manager_reorder_nodes'),
    path('bot-manager/reorder/node/<int:node_id>/options/', reorder_options, name='bot_manager_reorder_options'),
    path('servicios-manager/', service_manager, name='service_manager'),
    path('servicios-manager/create/', create_service, name='service_manager_create_service'),
    path('servicios-manager/<int:service_id>/update/', update_service, name='service_manager_update_service'),
    path('servicios-manager/<int:service_id>/delete/', delete_service, name='service_manager_delete_service'),
    path('servicios-manager/<int:service_id>/horarios/create/', create_weekly_range, name='service_manager_create_weekly_range'),
    path('servicios-manager/horarios/<int:range_id>/update/', update_weekly_range, name='service_manager_update_weekly_range'),
    path('servicios-manager/horarios/<int:range_id>/delete/', delete_weekly_range, name='service_manager_delete_weekly_range'),
    path('servicios-manager/<int:service_id>/excepciones/create/', create_exception, name='service_manager_create_exception'),
    path('servicios-manager/excepciones/<int:exception_id>/update/', update_exception, name='service_manager_update_exception'),
    path('servicios-manager/excepciones/<int:exception_id>/delete/', delete_exception, name='service_manager_delete_exception'),
    path('servicios-manager/<int:service_id>/paquetes/create/', create_package, name='service_manager_create_package'),
    path('servicios-manager/paquetes/<int:package_id>/update/', update_package, name='service_manager_update_package'),
    path('servicios-manager/paquetes/<int:package_id>/delete/', delete_package, name='service_manager_delete_package'),
]
