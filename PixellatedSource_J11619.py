import numpy,pyfits,pylab
import indexTricks as iT
from pylens import MassModels,pylens,adaptTools as aT,pixellatedTools as pT
from imageSim import SBModels,convolve
from scipy.sparse import diags
import pymc,cPickle
from scipy import optimize
import updateEmcee as myEmcee
import numpy as np, pylab as pl, pyfits as py
from pylens import lensModel
from scipy.interpolate import RectBivariateSpline


img1 = py.open('/data/ljo31/Lens/J1619/F606W_sci_cutout_big.fits')[0].data.copy()[50:-50,50:-50]
sig1 = py.open('/data/ljo31/Lens/J1619/F606W_noisemap_big.fits')[0].data.copy()[50:-50,50:-50]
psf1 = py.open('/data/ljo31/Lens/J1619/F606W_psf1.fits')[0].data.copy()
psf1 = psf1/np.sum(psf1)
img2 = py.open('/data/ljo31/Lens/J1619/F814W_sci_cutout_big.fits')[0].data.copy()[50:-50,50:-50]
sig2 = py.open('/data/ljo31/Lens/J1619/F814W_noisemap_big.fits')[0].data.copy()[50:-50,50:-50]
psf2 = py.open('/data/ljo31/Lens/J1619/F814W_psf4big.fits')[0].data.copy()
psf2 = psf2/np.sum(psf2)


imgs = [img1,img2]
sigs = [sig1,sig2]
psfs = [psf1,psf2]

PSFs = []
for i in range(len(imgs)):
    psf = psfs[i]
    image = imgs[i]
    psf /= psf.sum()
    psf = convolve.convolve(image,psf)[1]
    PSFs.append(psf)

OVRS = 1
yc,xc = iT.overSample(img1.shape,OVRS)
yo,xo = iT.overSample(img1.shape,1)
xo,xc=xo+15,xc+15
yo,yc=yo+10,yc+10
mask = py.open('/data/ljo31/Lens/J1619/mask.fits')[0].data.copy()[50:-50,50:-50]
tck = RectBivariateSpline(yo[:,0],xo[0],mask)
mask2 = tck.ev(xc,yc)
mask2[mask2<0.5] = 0
mask2[mask2>0.5] = 1
mask2 = mask2==0
mask = mask==0

guiFile = '/data/ljo31/Lens/J1619/gui_25c'
G,L,S,offsets,shear = numpy.load(guiFile)
X=26
result = np.load('/data/ljo31/Lens/J1619/emcee'+str(X))

lp= result[0]
print lp[:,0].shape
a1,a3 = numpy.unravel_index(lp[:,0].argmax(),lp[:,0].shape)
a2=0
trace = result[1]
dic = result[2]

gals = []
for name in G.keys():
    s = G[name]
    p = {}
    if name == 'Galaxy 1':
        for key in 'x','y','q','pa','re','n':
            p[key] = dic[name+' '+key][a1,a2,a3]
    elif name == 'Galaxy 2':
        for key in 'q','pa','re','n':
            p[key] = dic[name+' '+key][a1,a2,a3]
        for key in 'x','y':
            p[key]=gals[0].pars[key]
    elif name == 'Galaxy 3':
        for key in 'q','pa','re','n':
            p[key] = dic[name+' '+key][a1,a2,a3]
        for key in 'x','y':
            p[key]=gals[0].pars[key]
    gals.append(SBModels.Sersic(name,p))

lenses = []
for name in L.keys():
    s = L[name]
    p = {}
    for key in 'q','pa','b','eta','x','y':
        p[key] = dic[name+' '+key][a1,a2,a3]
    lenses.append(MassModels.PowerLaw(name,p))
p = {}
p['x'] = lenses[0].pars['x']
p['y'] = lenses[0].pars['y']
p['b'] = dic['extShear'][a1,a2,a3]
p['pa'] = dic['extShear PA'][a1,a2,a3]
lenses.append(MassModels.ExtShear('shear',p))

srcs = []
for name in S.keys():
    s = S[name]
    p = {}
    if name == 'Source 1':
        for key in 'q','re','n','pa':
           p[key] = dic[name+' '+key][a1,a2,a3]
        for key in 'x','y': # subtract lens potition - to be added back on later in each likelihood iteration!
            p[key] = dic[name+' '+key][a1,a2,a3]+lenses[0].pars[key]
    elif name == 'Source 2':
        for key in 'q','re','n','pa':
           p[key] = dic[name+' '+key][a1,a2,a3]
        for key in 'x','y': # subtract lens potition - to be added back on later in each likelihood iteration!
            p[key] = srcs[0].pars[key]
    srcs.append(SBModels.Sersic(name,p))

### first parameters need to be the offsets
xoffset =  dic['xoffset'][a1,a2,a3]
yoffset = dic['yoffset'][a1,a2,a3]

galsubs = []
for i in range(len(imgs)):
    if i == 0:
        dx,dy = 0,0
    else:
        dx = xoffset
        dy = yoffset
    xp,yp = xc+dx,yc+dy
    xop,yop = xo+dy,yo+dy
    image = imgs[i]
    sigma = sigs[i]
    psf = PSFs[i]
    imin,sigin,xin,yin = image.flatten(), sigma.flatten(),xp.flatten(),yp.flatten()
    n = 0
    model = np.empty(((len(gals) + len(srcs)),imin.size))
    for gal in gals:
        gal.setPars()
        tmp = xc*0.
        tmp = gal.pixeval(xp,yp,1./OVRS,csub=11) # evaulate on the oversampled grid. OVRS = number of new pixels per old pixel.
        tmp = iT.resamp(tmp,OVRS,True) # convert it back to original size
        tmp = convolve.convolve(tmp,psf,False)[0]
        model[n] = tmp.ravel()
        n +=1
    for lens in lenses:
        lens.setPars()
    x0,y0 = pylens.lens_images(lenses,srcs,[xp,yp],1./OVRS,getPix=True)
    for src in srcs:
        src.setPars()
        tmp = xc*0.
        tmp = src.pixeval(x0,y0,1./OVRS,csub=11)
        tmp = iT.resamp(tmp,OVRS,True)
        tmp = convolve.convolve(tmp,psf,False)[0]
        model[n] = tmp.ravel()
        n +=1
    rhs = (imin/sigin) 
    op = (model/sigin).T 
    fit, chi = optimize.nnls(op,rhs)
    components = (model.T*fit).T.reshape((n,image.shape[0],image.shape[1]))
    n = 0
    galim = image.copy()
    for n in range(len(gals)):
        galim -=components[n]
    galsubs.append(galim)

# we want the F814W image
galsub = galsubs[1]
#pl.figure()
#pl.imshow(galsub,origin='lower')
#py.writeto('/data/ljo31/Lens/J1619/galsub.fits',galsub)
# and a mask
mask = py.open('/data/ljo31/Lens/J1619/maskforpix.fits')[0].data.copy()
print mask.shape
mask = mask==1
Npnts = 1  # Defines `fineness' of source reconstruction (bigger is coarser)

# Function to make a `nice' plot
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

    osrc = src.eval(ox.ravel(),oy.ravel(),fit).reshape(ox.shape)

    oimg = img*numpy.nan
    oimg[mask] = (lmat*fit)

    ext = [0,img.shape[1],0,img.shape[0]]
    ext2 = [x.mean()-span/2.,x.mean()+span/2.,y.mean()-span/2.,y.mean()+span/2.]
    pylab.figure()
    pylab.subplot(221)
    img[~mask] = numpy.nan
    pylab.imshow(img,origin='lower',interpolation='nearest',extent=ext,cmap='jet')
    pylab.colorbar()
    pylab.subplot(222)
    pylab.imshow(oimg,origin='lower',interpolation='nearest',extent=ext,cmap='jet')
    pylab.colorbar()
    pylab.subplot(223)
    pylab.imshow((img-oimg)/sig,origin='lower',interpolation='nearest',extent=ext,cmap='jet')
    pylab.colorbar()
    pylab.subplot(224)
    pylab.imshow(osrc,origin='lower',interpolation='nearest',extent=ext2,cmap='jet')
    pylab.colorbar()
    return osrc

# Setup data for adaptive source modelling
img,sig,psf = galsub, sig2,psf2
#pl.figure()
#pl.imshow(img)
y,x = iT.coords(img.shape)
y,x=y+10,x+15
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
osrc = showRes(xl,yl,src,PSFm,img,sig,mask,ifltm,vfltm,cmatm,1e-5,1,400)
pylab.show()
'''

G,L,S,offsets,shear = numpy.load(guiFile)
pars = []
cov = []
lenses = []
for name in L.keys():
    model = L[name]
    lpars = {}
    for key in 'x','y','q','pa','b','eta':
        lo,hi = model[key]['lower'],model[key]['upper']
        val = dic[name+' '+key][a1,a2,a3]
        pars.append(pymc.Uniform('%s:%s'%(name,key),lo,hi,value=val))
        lpars[key] = pars[-1]
        cov.append(model[key]['sdev'])
    lenses.append(MassModels.PowerLaw(name,lpars))

if shear[1]==1:
    model = shear[0]
    spars = {}
    for key in 'pa','b':
        if key=='b':
            lo,hi = model[key]['lower'],model[key]['upper']
            val = dic['extShear'][a1,a2,a3]
            print lo,val,hi
            pars.append(pymc.Uniform('shear:%s'%(key),lo,hi,value=val))
            spars[key] = pars[-1]
            cov.append(model[key]['sdev'])
        elif key=='pa':
            lo,hi = model[key]['lower'],model[key]['upper']
            val = dic['extShear PA'][a1,a2,a3]
            print lo,val,hi
            pars.append(pymc.Uniform('shear:%s'%(key),lo,hi,value=val))
            spars[key] = pars[-1]
            cov.append(model[key]['sdev'])
    for key in 'x','y':
        spars[key] = lenses[0].pars[key]
    lenses.append(MassModels.ExtShear('shear',spars))


reg=1e-5
previousResult = None

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
    #print reg
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


@pymc.observed
def likelihood(value=0.,tmp=pars):
    return doFit(None,True,False,True,False)

cov = numpy.array(cov)
if previousResult is not None:
    result = numpy.load(previousResult)
    lp = result[0]
    trace = numpy.array(result[1])
    a1,a2 = numpy.unravel_index(lp.argmax(),lp.shape)
    for i in range(len(pars)):
        pars[i].value = trace[a1,a2,i]
    ns,nw,np = trace.shape
    cov = numpy.cov(trace[ns/2:].reshape((ns*nw/2,np)).T)

print 'about to do doFit'

doFit(None,True,True,False)
doFit(None,True,True,False)

print 'done doFit'

xl,yl = pylens.getDeflections(lenses,coords)
src.update(xl,yl)
osrc = showRes(xl,yl,src,PSFm,img,sig,mask,ifltm,vfltm,cmatm,reg,10,400)
pylab.show()
'''

'''
#reg *= 10.
S = myEmcee.Emcee(pars+[likelihood],cov=cov,nthreads=5,nwalkers=20)
S.sample(300)

print 'done emcee'
outFile = '/data/ljo31/Lens/J1619/pixsrc'

f = open(outFile,'wb')
cPickle.dump(S.result(),f,2)
f.close()

print 'cPickled!'

result = S.result()
lp = result[0]
trace = numpy.array(result[1])
a1,a2 = numpy.unravel_index(lp.argmax(),lp.shape)
for i in range(len(pars)):
    pars[i].value = trace[a1,a2,i]
    print "%18s  %8.3f"%(pars[i].__name__,pars[i].value)

print 'should have printed parametrers now...!'

xl,yl = pylens.getDeflections(lenses,coords)
src.update(xl,yl)
osrc = showRes(xl,yl,src,PSFm,img,sig,mask,ifltm,vfltm,cmatm,reg,0,400)
pylab.show()

print 'das Ende'
pl.figure()
pl.plot(lp)

'''
