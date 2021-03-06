from tools import solarmag
import numpy as np, pylab as pl, pyfits as py
import cPickle
from makemodel import *
from astLib import astCalc
from imageSim import SBObjects
from itertools import product

def run(Mstar,n,re_nugg,q,scale,z,mu_nugg):

    # construct nugget and normal galaxy - both have the same stellar mass and sit in identical haloes
    gal1 = SBObjects.Sersic('nugget',{'x':0,'y':0,'re':re1,'n':n1,'q':q1,'pa':pa1,'amp':1.})
    gal2 = SBObjects.Sersic('nugget',{'x':0,'y':0,'re':re2,'n':n2,'q':q2,'pa':pa2,'amp':1.})
    gal1.setAmpFromMag(mag1,48.60)
    gal2.setAmpFromMag(mag2,48.60)

    # get halo mass at z=0.5
    Mhalo = buildhalo(10**Mstar)
    rhalo = virialRadius(Mhalo,z)    

    # mass component - nugget
    r = np.logspace(-5,5,1501)
    sb1 = gal1.eval(r)
    sb2 = gal2.eval(r)
    lr,light_nugg = deproject(r,sb1+sb2) # assuming spherical symmetry - so will only be approximately right!
    Mdm = NFW(lr,rhalo,Mhalo)
    Mlum_nugg = light2mass(lr,light_nugg,1.)
    fac = Mlum_nugg[-1]/10**Mstar
    Mlum_nugg /= fac

    # take sigma within the effective radius of the galaxy
    sigma_dm_nugg = veldisp(r,sb_nugg,Mdm,ap=gal_nugg.re)
    sigma_star_nugg = veldisp(r,sb_nugg,Mlum_nugg,ap=gal_nugg.re)  
    vd_nugg = (sigma_dm_nugg + sigma_star_nugg)**0.5

    # m/l = 1 - could improve this by working out their MLs
    #mag_sol = solarmag.getmag('F606W_ACS',z)
    #mag = -2.5*Mstar + mag_sol - 5. + 5.*np.log10(astCalc.dl(0.55)*1e6)
    
    # SB
    #re_nugg_arcsec = re_nugg / scale
    #mu_nugg = mag + 2.5*np.log10(2.*np.pi*re_nugg_arcsec**2.)
    cat_nugg.append([re_nugg, vd_nugg, mu_nugg])
    print  '%.2f'%mu_nugg, '%.2f'%re_nugg, '%.2f'%vd_nugg, '%.2f'%n

masses = np.load('/data/ljo31b/EELs/inference/new/huge/masses_211.npy')
logM = masses[3]

sz = np.load('/data/ljo31/Lens/LensParams/SourceRedshiftsUpdated_1.00_lens_vdfit.npy')[()]
phot = py.open('/data/ljo31/Lens/LensParams/Phot_1src_huge_new_new.fits')[1].data
names = phot['name']
table = np.load('/data/ljo31/Lens/LensParams/Structure_1src_huge_new.npy')
re = np.array([table[0][name]['Source 1 re'] for name in names])
ns = np.array([table[0][name]['Source 1 n'] for name in names])
scales = np.array([astCalc.da(sz[name][0])*1e3*np.pi/180./3600. for name in names])
re *= 0.05*scales
qs = np.array([table[0][name]['Source 1 q'] for name in names])
mus = phot['mu v']


cat_norm, cat_nugg = [], []


for i in range(logM.size):
    run(logM[i],n=ns[i],re_nugg=re[i],q=qs[i],scale=scales[i],z=sz[names[i]][0],mu_nugg = mus[i])

np.savetxt('/data/ljo31b/EELs/phys_models/FP_nuggets_realeels.dat',cat_nugg)


