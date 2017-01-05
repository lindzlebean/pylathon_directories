import glob,cPickle,numpy
from spsmodels import zspsmodel as spsmodel
from scipy import interpolate
import sys,time
import numpy as np

# Grab the SED models
files = glob.glob('/data/mauger/STELLARPOP/chabrier_Z*dat')
axes = {'Z':[],'age':None,'tau':None,'tau_V':None}

for file in files:
    z = float(file.split('=')[1].split('.dat')[0])
    axes['Z'].append(z)
axes['Z'] = numpy.sort(numpy.unique(numpy.asarray(axes['Z'])))

# We could open any of the files; they'll all have the same tau, tau_V, age
#   arrays.
f = open(file)
tmp = cPickle.load(f) # Trash read of output
del tmp
tmp = cPickle.load(f) # Trash read of wave
del tmp
t = cPickle.load(f)
tV = cPickle.load(f)
a = cPickle.load(f)
f.close()

axes['age'] = a
axes['tau'] = t
axes['tau_V'] = tV

# The interpolation order of the input data. Use linear (order=1) for the
#   crazy 'Z' sampling chosen by BC03.
order = {'Z':1,'age':3,'tau':3,'tau_V':3}
axes_models = {}
interpmodels = {}

for key in axes.keys():
    arr = axes[key]
    axes_models[key] = {}
    axes_models[key]['points'] = numpy.sort(arr)
    axes_models[key]['eval'] = interpolate.splrep(arr,numpy.arange(arr.size),k=order[key],s=0)

filters1 = ['g_SDSS','r_SDSS','i_SDSS','z_SDSS','Kp_NIRC2','F555W_ACS','F814W_ACS']
filters2 = ['g_SDSS','r_SDSS','i_SDSS','z_SDSS','Kp_NIRC2','F606W_ACS','F814W_ACS']
szs = np.load('/data/ljo31/Lens/LensParams/SourceRedshiftsUpdated.npy')[()]
lzs = np.load('/data/ljo31/Lens/LensParams/LensRedshiftsUpdated.npy')[()]
bands = np.load('/data/ljo31/Lens/LensParams/HSTBands.npy')[()]
'''for key in szs.keys():

    name,z = key, szs[key][0]
    redshift = float(z)
    print 'redshift', redshift

    outname = '/data/ljo31b/EELs/spsmodels/wide/'+name+'_source_chabBC03.model'
    finished = glob.glob('/data/ljo31b/EELs/spsmodels/wide/*_source_chabBC03.model')
    if outname in finished:
        print 'done already'
        continue
    f = open(outname,'wb')

    axes_models['redshift'] = {'points':numpy.array([redshift])}
    #print "Creating model: ",outname
    t = time.time()
    if bands[name] == 'F555W':
        model = spsmodel.zSPSModel(files,axes_models,filters1)
    elif bands[name] == 'F606W':
        model = spsmodel.zSPSModel(files,axes_models,filters2)
    else:
        print 'ERROR'
    cPickle.dump(model,f,2)
    f.close()
    print "Time elapsed: ",(time.time()-t)

for key in lzs.keys():
    name,z = key, lzs[key][0]
    redshift = float(z)
    print 'redshift', redshift

    outname = '/data/ljo31b/EELs/spsmodels/wide/'+name+'_lens_chabBC03.model'
    finished = glob.glob('/data/ljo31b/EELs/spsmodels/wide/*_lens_chabBC03.model')
    if outname in finished:
        continue
    f = open(outname,'wb')

    axes_models['redshift'] = {'points':numpy.array([redshift])}
    print "Creating model: ",outname
    t = time.time()
    if bands[name] == 'F555W':
        model = spsmodel.zSPSModel(files,axes_models,filters1)
    elif bands[name] == 'F606W':
        model = spsmodel.zSPSModel(files,axes_models,filters2)
    else:
        print 'ERROR'
    cPickle.dump(model,f,2)
    f.close()
    print "Time elapsed: ",(time.time()-t)

# sdss source magnitudes 211
filters1 = ['g_SDSS','r_SDSS','i_SDSS','z_SDSS','Kp_NIRC2','F555W_ACS','F814W_ACS']
filters2 = ['g_SDSS','r_SDSS','i_SDSS','z_SDSS','Kp_NIRC2','F606W_ACS','F814W_ACS']
magnifications = np.load('/data/ljo31/Lens/LensParams/magnifications_211_huge.npy')[()]
szs = np.load('/data/ljo31/Lens/LensParams/SourceRedshiftsUpdated.npy')[()]
for key in szs.keys():
    if key == 'J1248':
        continue
    name,z,mu = key, szs[key][0],magnifications[key][0]
    redshift = float(z)
    if bands[name] == 'F555W':
        filts = filters1
    elif bands[name] == 'F606W':
        filts = filters2
    else:
        print 'ERROR'
    mus = []
    for j in range(len(filts)):
        if filts[j][2:] == 'SDSS':
            mus.append((filts[j],mu))
        else:
            mus.append((filts[j],1))
    mus = dict(mus)
    print mus
    
    outname = '/data/ljo31b/EELs/spsmodels/wide/'+name+'_source_211_chabBC03.model'
    finished = glob.glob('/data/ljo31b/EELs/spsmodels/wide/*_source_211_chabBC03.model')
    if outname in finished:
        print name, 'already done'
        continue
    f = open(outname,'wb')

    axes_models['redshift'] = {'points':numpy.array([redshift])}
    print "Creating model: ",outname
    t = time.time()
    model = spsmodel.zSPSModel(files,axes_models,filts,mu=mus)

    cPickle.dump(model,f,2)
    f.close()
    print "Time elapsed: ",(time.time()-t)
'''
# sdss source magnitudes 212
magnifications = np.load('/data/ljo31/Lens/LensParams/magnifications_212_huge.npy')[()]
szs = np.load('/data/ljo31/Lens/LensParams/SourceRedshiftsUpdated.npy')[()]
for key in szs.keys():
    if key == 'J1248':
        continue
    name,z,mu = key, szs[key][0],magnifications[key][0]
    redshift = float(z)
    
    if bands[name] == 'F555W':
        filts = filters1
    elif bands[name] == 'F606W':
        filts = filters2
    else:
        print 'ERROR'
    mus = []
    for j in range(len(filts)):
        if filts[j][2:] == 'SDSS':
            mus.append((filts[j],mu))
        else:
            mus.append((filts[j],1))
    mus = dict(mus)
    print mus

    outname = '/data/ljo31b/EELs/spsmodels/wide/'+name+'_source_212_chabBC03.model'
    finished = glob.glob('/data/ljo31b/EELs/spsmodels/wide/*_source_212_chabBC03.model')
    if outname in finished:
        continue
    f = open(outname,'wb')

    axes_models['redshift'] = {'points':numpy.array([redshift])}
    print "Creating model: ",outname
    t = time.time()
    model = spsmodel.zSPSModel(files,axes_models,filts,mu=mus)

    cPickle.dump(model,f,2)
    f.close()
    print "Time elapsed: ",(time.time()-t)


