import numpy,pyfits,pylab
import indexTricks as iT
from pylens import MassModels,pylens,adaptTools as aT,pixellatedTools as pT
from imageSim import SBModels,convolve
from scipy.sparse import diags
import pymc,cPickle
from scipy import optimize
import myEmcee_blobs as myEmcee 
import numpy as np, pylab as pl, pyfits as py
from pylens import lensModel
from scipy.interpolate import RectBivariateSpline
import adaptToolsBug as BB
from linslens.pixplot import *

def showRes(x,y,src,psf,img,sig,mask,iflt,vflt,cmat,reg,niter,npix):
    oy,ox = iT.coords((npix,npix))
    oy -= oy.mean()
    ox -= ox.mean()
    span = max(x.max()-x.min(),y.max()-y.min())
    oy *= span/npix
    ox *= span/npix
    ox += x.mean()
    oy += y.mean()
    lmat = psf*src.lmat
    rmat = src.rmat
    print reg
    res,fit,model,rhs,regg = aT.getModelG(iflt,vflt,lmat,cmat,rmat,reg,niter=niter)
    print regg
    osrc = src.eval(ox.ravel(),oy.ravel(),fit).reshape(ox.shape)

    oimg = img*numpy.nan
    oimg[mask] = (lmat*fit)

    ext = [0,img.shape[1],0,img.shape[0]]
    ext2 = [x.mean()-span/2.,x.mean()+span/2.,y.mean()-span/2.,y.mean()+span/2.]

    # for paper -- just model in the two planes?
    pylab.figure(figsize=(5,8))
    pylab.subplot(211)
    pl.figtext(0.075,0.9,'J1125')
    pylab.imshow(oimg[40:-40,40:-40],origin='lower',interpolation='nearest',extent=ext,vmin=0,vmax=1,cmap='jet',aspect='auto')
    #ax = pl.axes()
    #ax.set_xticklabels([])
    #ax.set_yticklabels([])
    pl.gca().xaxis.set_major_locator(pl.NullLocator())
    pl.gca().yaxis.set_major_locator(pl.NullLocator())
    pylab.colorbar()
    pylab.subplot(212)
    pylab.imshow(osrc,origin='lower',interpolation='nearest',extent=ext2,vmin=0,vmax=2.,cmap='jet',aspect='auto')
    pl.gca().xaxis.set_major_locator(pl.NullLocator())
    pl.gca().yaxis.set_major_locator(pl.NullLocator())
    pylab.colorbar()

    pylab.figure()
    pylab.subplot(221)
    img[~mask] = numpy.nan
    pylab.imshow(img[40:-40,40:-40],origin='lower',interpolation='nearest',extent=ext,vmin=0,vmax=1,cmap='jet',aspect='auto')
    pylab.colorbar()
    pylab.subplot(222)
    pylab.imshow(oimg[40:-40,40:-40],origin='lower',interpolation='nearest',extent=ext,vmin=0,vmax=1,cmap='jet',aspect='auto')
    pylab.colorbar()
    pylab.subplot(223)
    pylab.imshow((img[40:-40,40:-40]-oimg[40:-40,40:-40])/sig[40:-40,40:-40],origin='lower',interpolation='nearest',extent=ext,vmin=-3,vmax=3,cmap='jet',aspect='auto')
    pylab.colorbar()
    pylab.subplot(224)
    pylab.imshow(osrc,origin='lower',interpolation='nearest',extent=ext2,vmin=0,vmax=1,cmap='jet',aspect='auto')
    pylab.colorbar()

    return osrc


img = py.open('/data/ljo31/Lens/J1125/galsub_0.fits')[0].data.copy()
sig = py.open('/data/ljo31/Lens/J1125/F606W_noisemap_huge2.fits')[0].data.copy()[50:-50,50:-50][50:-50,50:-50]
psf = py.open('/data/ljo31/Lens/J1125/F606W_psf3_filledin.fits')[0].data.copy()
psf = psf[5:-7,5:-6]
psf = psf/np.sum(psf)
Dx,Dy = -85,-85

# pixellated source modelling mask
mask = py.open('/data/ljo31/Lens/J1125/maskneu.fits')[0].data.copy()#[50:-50,50:-50]
mask = mask==1
Npnts = 2  # Defines `fineness' of source reconstruction (bigger is coarser)

result = np.load('/data/ljo31/Lens/J1125/pixsrc_neu4')

lp,trace,dic,_= result
a1,a3 = np.unravel_index(lp[:,0].argmax(),lp[:,0].shape)

lenses = []
p = {}
for key in 'x','y','q','pa','b','eta':
    p[key] = dic['Lens 1 '+key][a1,0,a3]
lenses.append(MassModels.PowerLaw('Lens 1',p))
p = {}
p['x'] = lenses[0].pars['x']
p['y'] = lenses[0].pars['y']
p['b'] = dic['extShear'][a1,0,a3] 
p['pa'] = dic['extShear PA'][a1,0,a3]
lenses.append(MassModels.ExtShear('shear',p))


import time
def doFit(p=None,doReg=True,updateReg=True,checkImgs=True,levMar=False):
    global reg
    # Check if using levMar-style parameters
    if p is not None:
        for i in range(len(p)):
            pars[i].value = p[i]
            # If the parameter is out-of-bounds return a bad fit
            try:
                a = pars[i].logp
            except:
                return iflt/sflt

    for l in lenses:
        l.setPars()
    xl,yl = pylens.getDeflections(lenses,coords)

    src.update(xl,yl,doReg=doReg)
    lmat = PSFm*src.lmat
    if doReg==True:
        rmat = src.rmat
    else:
        rmat = None
    nupdate = 0
    if doReg==True and updateReg==True:
        nupdate = 10
    res,fit,model,_,regg = aT.getModelG(ifltm,vfltm,lmat,cmatm,rmat,reg,nupdate)
    reg = regg[0]
    if checkImgs is False:
        if levMar:
            res = res**0.5+ifltm*0.
        return -0.5*res
    # This checks is images are formed outside of the masked region
    xl,yl = pylens.getDeflections(lenses,[xflt,yflt])
    oimg,pix = src.eval(xl,yl,fit,domask=False)
    oimg = PSF*oimg
    res = (iflt-oimg)/sflt
    if levMar:
        return res
    return -0.5*(res**2).sum()

# Setup data for adaptive source modelling
y,x = iT.coords(img.shape)
x=x+Dx+50
y=y+Dy+50
cpsf = convolve.convolve(img,psf)[1]
ifltm = img[mask]
sfltm = sig[mask]
vfltm = sfltm**2
cmatm = diags(1./sfltm,0)
xm = x[mask]
ym = y[mask]
coords = [xm,ym]

PSF = pT.getPSFMatrix(psf,img.shape)
PSFm = pT.maskPSFMatrix(PSF,mask)

iflt = img.flatten()
sflt = sig.flatten()
vflt = sflt**2

xflt = x.flatten()
yflt = y.flatten()

src = aT.AdaptiveSource(ifltm/sfltm,ifltm.size/Npnts)
xl,yl = pylens.getDeflections(lenses,coords)
src.update(xl,yl)
# regularise
reg=1.
doFit(None,True,True,True,False)
doFit(None,True,True,True,False)
chi2 = doFit(None,True,True,True,False)
print chi2
print reg
xl,yl = pylens.getDeflections(lenses,coords)
src.update(xl,yl)
osrc = showRes(xl,yl,src,PSFm,img,sig,mask,ifltm,vfltm,cmatm,reg,5,100)

pl.figure()
pl.plot(lp[:,0])
pylab.show()

