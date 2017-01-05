import numpy as np, pylab as pl, pyfits as py
'''
phot = py.open('/data/ljo31/Lens/LensParams/Phot_2src_huge_firsthalf.fits')[1].data
NAMES = phot['name']
re,mu = phot['Re v'], phot['mu v']

photold = py.open('/data/ljo31/Lens/LensParams/Phot_2src_new.fits')[1].data
names = photold['name']
reold,muold = photold['Re v'][:8], photold['mu v'][:8]


pl.figure()
pl.scatter(re,re-reold,c='CornflowerBlue',s=30)
pl.scatter(mu,mu-muold,c='Crimson',s=30)
pl.axhline(0)
'''

# 211
result = np.load('/data/ljo31/Lens/J1347/twoband_3')
lp,trace,dic,_= result

# 212
result = np.load('/data/ljo31/Lens/J1347/twoband_212_really_0')
lp,trace,dic2,_= result

# 112
result = np.load('/data/ljo31/Lens/J1347/twoband_212_2')
lp,trace,dic3,_= result

