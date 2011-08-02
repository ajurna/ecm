# Copyright (c) 2010-2011 Robin Jarry
# 
# This file is part of EVE Corporation Management.
# 
# EVE Corporation Management is free software: you can redistribute it and/or 
# modify it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or (at your 
# option) any later version.
# 
# EVE Corporation Management is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY 
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for 
# more details.
# 
# You should have received a copy of the GNU General Public License along with 
# EVE Corporation Management. If not, see <http://www.gnu.org/licenses/>.

__date__ = "2011 6 26"
__author__ = "diabeteman"

import json

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models.aggregates import Count
from django.contrib.auth.models import User
from django.conf import settings

from ecm.view.decorators import basic_auth_required
from ecm.data.common.models import ExternalApplication, GroupBinding

#------------------------------------------------------------------------------
@basic_auth_required(username=settings.CRON_USERNAME)
def players(request):
    query = User.objects.select_related(depth=3).filter(is_active=True)
    query = query.annotate(char_count=Count("characters"))
    query = query.filter(char_count__gt=0)
    query = query.exclude(username__in=[settings.CRON_USERNAME, settings.ADMIN_USERNAME])
    members = []
    for player in query:
        characters = list(player.characters.values('name', 
                                                   'characterID'))
        characters.sort(key=lambda x: x['name'].lower())
        bindings = list(player.bindings.values('external_app__name', 
                                               'external_name', 
                                               'external_id'))
        members.append({
            'id': player.id,
            'username': player.username, 
            'characters': characters,
            'bindings': bindings
        })
    return HttpResponse(json.dumps(members))

#------------------------------------------------------------------------------
@basic_auth_required(username=settings.CRON_USERNAME)
def user_bindings(request, app_name):
    app = get_object_or_404(ExternalApplication, name=app_name)
    query = app.user_bindings.select_related(depth=3)
    query = query.annotate(char_count=Count("user__characters"))
    query = query.filter(user__is_active=True)
    query = query.filter(char_count__gt=0)
    
    group_bindings = {}
    for gb in GroupBinding.objects.filter(external_app=app):
        group_bindings[gb.group] = gb
    
    members = []
    for binding in query:
        characters = list(binding.user.characters.values('name', 
                                                         'characterID'))
        characters.sort(key=lambda x: x['name'].lower())
        
        groups = set()
        for g in binding.user.groups.all():
            try: groups.add(group_bindings[g].external_id)
            except KeyError: pass
        
        members.append({
            'external_id': binding.external_id,
            'external_name': binding.external_name, 
            'groups': list(groups),
            'characters': characters,
        })
    return HttpResponse(json.dumps(members))

#------------------------------------------------------------------------------
@basic_auth_required(username=settings.CRON_USERNAME)
def group_bindings(request, app_name):
    app = get_object_or_404(ExternalApplication, name=app_name)
    groups = GroupBinding.objects.filter(external_app=app)
    groups = groups.values('external_name', 'external_id').distinct()
    return HttpResponse(json.dumps(list(groups)))
