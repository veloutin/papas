# PAPAS Access Point Administration System
# Copyright (c) 2010 Revolution Linux inc. <info@revolutionlinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls.defaults import *

urlpatterns = patterns ('apmanager.accesspoints',

    url(r'^$', 'views.ap.view_ap_list', name="home" ),

    (r'^clients/$', 'views.ap.view_client_list' ),
    
    (r'^(?P<ap_id>\d+)/$', 'views.ap.view_ap' ),

    (r'^init/$', 'views.ap.ap_init_overview' ),

    (r'^(?P<ap_id>\d+)/init/$', 'views.ap.view_ap_init' ),

    (r'^(?P<ap_id>\d+)/nagios/$', 'views.ap.view_ap_nagios_config'),

    (r'^nagios/$', 'views.ap.view_nagios_config'),
)
