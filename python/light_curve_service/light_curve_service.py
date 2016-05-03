"""
Tools for examining light curves from Level 2 tables using sncosmo.
"""
from __future__ import absolute_import, print_function
import os
from collections import OrderedDict
import numpy as np
import astropy.table
import astropy.units
import matplotlib.pyplot as plt
import sncosmo
import desc.pserv

__all__ = ['LightCurve', 'LightCurveFactory']

def bandpass(band):
    "LSST band pass name"
    return 'lsst%s' % band

class LightCurve(object):
    "Multiband light curve using sncosmo."
    def __init__(self, lc_dict):
        """
        lc_dict: light curve data from the ForcedSource table.
        """
        data = dict([(key, []) for key in
                     'bandpass mjd ra dec flux fluxerr zp zpsys'.split()])
        for band, lc_recarr in lc_dict.items():
            npts = len(lc_recarr)
            data['bandpass'].extend(npts*[bandpass(band)])
            for key in 'mjd ra dec flux fluxerr'.split():
                data[key].extend(lc_recarr[key])
            data['zp'].extend(npts*[25.0])
            data['zpsys'].extend(npts*['ab'])
        self.data = astropy.table.Table(data=data)

    def plot(self, **kwds):
        "Plot the light curve data."
        kwds['data'] = self.data
        fig = sncosmo.plot_lc(**kwds)
        return fig

class LightCurveFactory(object):
    def __init__(self, **db_info):
        "Connect to the ForcedSource db table and fill the sncosmo registry."
        self.connection = desc.pserv.DbConnection(**db_info)
        self._fill_sncosmo_registry()

    def _fill_sncosmo_registry(self, bands='ugrizy'):
        "Fill the sncosmo registry with the LSST bandpass data."
        for band in bands:
            bp_file = os.path.join(os.environ['THROUGHPUTS_DIR'], 'baseline',
                                   'total_%s.dat' % band)
            bp_data = np.genfromtxt(bp_file, names=['wavelen', 'transmission'])
            band = sncosmo.Bandpass(bp_data['wavelen'],
                                    bp_data['transmission'],
                                    name=bandpass(band),
                                    wave_unit=astropy.units.nm)
            sncosmo.registry.register(band, force=True)

    def getObjectIds(self):
        "Get the objectIds in the reference catalog."
        query = 'select objectId from Object order by objectId asc'
        return self.connection.apply(query, lambda curs : [x[0] for x in curs])

    @staticmethod
    def _process_rows(cursor):
        results = []
        dtype = [('mjd', float), ('ra', float), ('dec', float),
                 ('flux', float), ('fluxerr', float), ('visit', int)]
        for entry in cursor:
            obs_start, ra, dec, flux, fluxerr, visit = tuple(entry)
            mjd = astropy.time.Time(obs_start).mjd
            results.append((mjd, ra, dec, flux, fluxerr, visit))
        results = np.array(results, dtype=dtype)
        return results

    def create(self, objectId):
        "Create a LightCurve object."
        light_curve_data = OrderedDict()
        for band in 'ugrizy':
            query = """select cv.obsStart, obj.psRa, obj.psDecl,
                    fs.psFlux, fs.psFlux_Sigma, fs.ccdVisitId
                    from CcdVisit cv join ForcedSource fs
                    on cv.ccdVisitId=fs.ccdVisitId join Object obj
                    on fs.objectId=obj.objectId
                    where cv.filterName='%(band)s' and fs.objectId=%(objectId)i
                    order by cv.obsStart asc""" % locals()
            light_curve_data[band] = self.connection.apply(query,
                                                           self._process_rows)
        return LightCurve(light_curve_data)
