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

__date__ = "2010-02-08"
__author__ = "diabeteman"




from ecm.data.corp.models import Corp, Hangar, Wallet
from ecm.core.eve import api

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from ecm.core.parsers.utils import checkApiVersion, markUpdated

import logging
logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------
@transaction.commit_manually
def update():
    """
    Fetch a /corp/CorporationSheet.xml.aspx api response, parse it and store it to 
    the database.
    """
    
    try:
        logger.info("fetching /corp/CorporationSheet.xml.aspx...")
        # connect to eve API
        api_conn = api.connect()
        # retrieve /corp/CorporationSheet.xml.aspx
        corpApi = api_conn.corp.CorporationSheet(characterID=api.get_api().charID)
        checkApiVersion(corpApi._meta.version)

        currentTime = corpApi._meta.currentTime
        cachedUntil = corpApi._meta.cachedUntil
        logger.debug("current time : %s", str(currentTime))
        logger.debug("cached util : %s", str(cachedUntil))

        logger.debug("parsing api response...")
        try: 
            allianceName = corpApi.allianceName
            allianceID   = corpApi.allianceID
            allianceTicker = ""
            alliancesApi = api_conn.eve.AllianceList()
            for a in alliancesApi.alliances:
                if a.allianceID == allianceID:
                    allianceTicker = a.shortName
                    break
        except:
            allianceName = "-"
            allianceID   = 0
            allianceTicker = "-"

        try:
            # try to retrieve the db stored corp info
            corp = Corp.objects.get(id=1)
            corp.corporationID   = corpApi.corporationID
            corp.corporationName = corpApi.corporationName
            corp.ticker          = corpApi.ticker
            corp.ceoID           = corpApi.ceoID
            corp.ceoName         = corpApi.ceoName
            corp.stationID       = corpApi.stationID
            corp.stationName     = corpApi.stationName
            corp.allianceID      = allianceID
            corp.allianceName    = allianceName
            corp.allianceTicker  = allianceTicker
            corp.description     = corpApi.description
            corp.taxRate         = corpApi.taxRate
            corp.memberLimit     = corpApi.memberLimit

        except ObjectDoesNotExist:
            # no corp parsed yet
            corp = Corp( id              = 1,
                         corporationID   = corpApi.corporationID, 
                         corporationName = corpApi.corporationName,
                         ticker          = corpApi.ticker,      
                         ceoID           = corpApi.ceoID,
                         ceoName         = corpApi.ceoName,
                         stationID       = corpApi.stationID,     
                         stationName     = corpApi.stationName,     
                         description     = corpApi.description,
                         allianceID      = allianceID,
                         allianceName    = allianceName,
                         allianceTicker  = allianceTicker,
                         taxRate         = corpApi.taxRate,      
                         memberLimit     = corpApi.memberLimit )
        
        corp.save()
        
        # we store the update time of the table
        markUpdated(model=Corp, date=currentTime)
        
        logger.debug("name: %s [%s]", corp.corporationName, corp.ticker)
        logger.debug("alliance: %s <%s>", corp.allianceName, corp.allianceTicker)
        logger.debug("CEO: %s", corpApi.ceoName)
        logger.debug("tax rate: %d%%", corp.taxRate)
        logger.debug("member limit: %d", corp.memberLimit)
            
        logger.debug("HANGAR DIVISIONS:")
        for hangarDiv in corpApi.divisions :
            h_id   = hangarDiv.accountKey
            h_name = hangarDiv.description
            try:
                h = Hangar.objects.get(hangarID=h_id)
                h.name = h_name
            except ObjectDoesNotExist:
                h = Hangar(hangarID=h_id, name=h_name)
            logger.debug("  %s [%d]", h.name, h.hangarID)
            h.save()
        
        # we store the update time of the table
        markUpdated(model=Hangar, date=currentTime)
        
        logger.debug("WALLET DIVISIONS:")
        for walletDiv in corpApi.walletDivisions :
            w_id   = walletDiv.accountKey
            w_name = walletDiv.description
            try:
                w = Wallet.objects.get(walletID=w_id)
                w.name = w_name
            except ObjectDoesNotExist:
                w = Wallet(walletID=w_id, name=w_name)
            logger.debug("  %s [%d]", w.name, w.walletID)
            w.save()
        
        # we store the update time of the table
        markUpdated(model=Wallet, date=currentTime)
        
        # all ok
        logger.debug("saving data to the database...")
        transaction.commit()
        logger.debug("DATABASE UPDATED!")
        logger.info("corp info updated")
    except:
        # error catched, rollback changes
        transaction.rollback()
        logger.exception("update failed")
        raise
