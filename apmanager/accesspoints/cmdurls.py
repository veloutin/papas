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


    (r'new/$', 'views.apcommands.create_new_command' ),

    (r'new/ap/(?P<ap_id>\d+)/cmd/(?P<command_id>\d+)/$', 'views.apcommands.edit_new_command' , {'group_id':None} ),
    (r'new/cmd/(?P<command_id>\d+)/ap/(?P<ap_id>\d+)/$', 'views.apcommands.edit_new_command' , {'group_id':None} ),

    (r'new/group/(?P<group_id>\d+)/cmd/(?P<command_id>\d+)/$', 'views.apcommands.edit_new_command' , {'ap_id':None} ),
    (r'new/cmd/(?P<command_id>\d+)/group/(?P<group_id>\d+)/$', 'views.apcommands.edit_new_command' , {'ap_id':None} ),

    (r'view/(?P<command_id>\d+)/$','views.apcommands.view_command'),
    (r'viewexec/(?P<exec_id>\d+)/$','views.apcommands.view_exec'),

    (r'all/?$', 'views.apcommands.view_home', dict(view_all=True) ),
    (r'$', 'views.apcommands.view_home' ),


)
