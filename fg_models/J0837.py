import cPickle,numpy,pyfits as py
import pymc
from pylens import *
from imageSim import SBModels,convolve,SBObjects
import indexTricks as iT
from SampleOpt import AMAOpt
import pylab as pl
import numpy as np
import myEmcee_blobs as myEmcee
from matplotlib.colors import LogNorm
from scipy import optimize
from scipy.interpolate import RectBivariateSpline
import SBBModels, SBBProfiles

''' the plan: to remodel the foreground light using a single Sersic component to use in the M/L modelling -- because we can't assign each Sersic component its own mass, that isn't really physical '''

X=2
print X

# plot things
def NotPlicely(image,im,sigma):
    ext = [0,image.shape[0],0,image.shape[1]]
    #vmin,vmax = numpy.amin(image), numpy.amax(image)
    pl.figure()
    pl.subplot(221)
    pl.imshow(image,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',aspect='auto',vmin=0,vmax=np.amax(image)*0.5) #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('data')
    pl.subplot(222)
    pl.imshow(im,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',aspect='auto',vmin=0,vmax=np.amax(image)*0.5) #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('model')
    pl.subplot(223)
    pl.imshow(image-im,origin='lower',interpolation='nearest',extent=ext,vmin=-0.25,vmax=0.25,cmap='afmhot',aspect='auto')
    pl.colorbar()
    pl.title('data-model')
    pl.subplot(224)
    pl.imshow((image-im)/sigma,origin='lower',interpolation='nearest',extent=ext,vmin=-5,vmax=5,cmap='afmhot',aspect='auto')
    pl.title('signal-to-noise residuals')
    pl.colorbar()

img1 = py.open('/data/ljo31/Lens/J0837/F606W_sci_cutout_huge.fits')[0].data.copy()[70:-70,70:-70]#[30:-30,30:-30] 
sig1 = py.open('/data/ljo31/Lens/J0837/F606W_noisemap_huge.fits')[0].data.copy()[70:-70,70:-70]#[50:-50,50:-50]#[30:-30,30:-30] 
psf1 = py.open('/data/ljo31/Lens/J0837/F606W_psf1.fits')[0].data.copy()
psf1 = psf1/np.sum(psf1)

img2 = py.open('/data/ljo31/Lens/J0837/F814W_sci_cutout_huge.fits')[0].data.copy()[70:-70,70:-70]#[50:-50,50:-50]#[30:-30,30:-30] 
sig2 = py.open('/data/ljo31/Lens/J0837/F814W_noisemap_huge.fits')[0].data.copy()[70:-70,70:-70]#[50:-50,50:-50]#[30:-30,30:-30] 
psf2 = py.open('/data/ljo31/Lens/J0837/F814W_psf3.fits')[0].data.copy()
psf2 = psf2/np.sum(psf2)

imgs = [img1,img2]
sigs = [sig1,sig2]
psfs = [psf1,psf2]
PSFs = []
for i in range(len(psfs)):
    psf = psfs[i]
    image = imgs[i]
    psf /= psf.sum()
    psf = convolve.convolve(image,psf)[1]
    PSFs.append(psf)


result = np.load('/data/ljo31/Lens/J0837/fg_model_1')
lp,trace,dic,_= result
a2=0
a1,a3 = numpy.unravel_index(lp[:,0].argmax(),lp[:,0].shape)

OVRS = 1
yc,xc = iT.overSample(img1.shape,OVRS)
yo,xo = iT.overSample(img1.shape,1)
yc,yo=yc-100,yo-100
xc,xo=xc-100,xo-100
xc,xo,yc,yo = xc+70,xo+70,yc+70,yo+70
mask = py.open('/data/ljo31/Lens/J0837/mask_huge.fits')[0].data[70:-70,70:-70]#[50:-50,50:-50]
tck = RectBivariateSpline(yo[:,0],xo[0],mask)
mask2 = tck.ev(xc,yc)
mask2[mask2<0.5] = 0
mask2[mask2>0.5] = 1
mask2 = mask2==0
mask = mask==0

print mask.shape, img1.shape

# galaxy is a free parameter. Lens deflections are calculated once, as are source profiles.

pars = []
cov = []

# offsets
DX,DY = dic['xoffset'][a1,a2,a3],dic['yoffset'][a1,a2,a3]

# source
srcs = []
name = 'Source 1'
p = {}
for key in 'q','re','n','pa':
    p[key] = dic[name+' '+key][a1,a2,a3]
p['x'] = dic['Source 1 x'][a1,a2,a3] + dic['Lens 1 x'][a1,a2,a3]
p['y'] = dic['Source 1 y'][a1,a2,a3] + dic['Lens 1 y'][a1,a2,a3]
srcs.append(SBModels.Sersic(name,p))

name = 'Source 2'
p = {}
for key in 'q','re','n','pa','x','y':
    p[key] = dic[name+' '+key][a1,a2,a3]
srcs.append(SBModels.Sersic(name,p))

lenses = []
p = {}
for key in 'x','y','q','pa','b','eta':
    p[key] = dic['Lens 1 '+key][a1,a2,a3]
lenses.append(MassModels.PowerLaw('Lens 1',p))

SH = dic['extShear'][a1,a2,a3]
SHPA = dic['extShear PA'][a1,a2,a3]
shear = MassModels.ExtShear('shear',{'x':lenses[0].x,'y':lenses[0].y,'b':SH,'pa':SHPA})
lenses += [shear]

XG1 = pymc.Uniform('Galaxy 1 x',dic['Galaxy 1 x'][a1,a2,a3]-10,dic['Galaxy 1 x'][a1,a2,a3]+10,dic['Galaxy 1 x'][a1,a2,a3])
YG1 = pymc.Uniform('Galaxy 1 y',dic['Galaxy 1 y'][a1,a2,a3]-10,dic['Galaxy 1 y'][a1,a2,a3]+10,dic['Galaxy 1 y'][a1,a2,a3])
QG1 = pymc.Uniform('Galaxy 1 q',0.1,1.,dic['Galaxy 1 q'][a1,a2,a3])
PAG1 = pymc.Uniform('Galaxy 1 pa',-180.,180.,dic['Galaxy 1 pa'][a1,a2,a3])
REG1 = pymc.Uniform('Galaxy 1 re',0,100,20.)
NG1 = pymc.Uniform('Galaxy 1 n',0.5,8,3.5)
gal1 = SBModels.Sersic('Galaxy 1',{'x':XG1,'y':YG1,'q':QG1,'pa':PAG1,'re':REG1,'n':NG1})
gals = [gal1]
pars += [XG1,YG1,QG1,PAG1,REG1,NG1]
cov += [0.5,0.5,0.1,1.,5.,1]

# pre-calculate most things
xin1,yin1 = xc[mask2],yc[mask2]
xin2,yin2 = (xc+DX)[mask2], (yc+DY)[mask2]
print mask2.shape
for lens in lenses:
    lens.setPars()
x0V,y0V = pylens.lens_images(lenses,srcs,[xin1,yin1],1./OVRS,getPix=True)
x0I,y0I = pylens.lens_images(lenses,srcs,[xin2,yin2],1./OVRS,getPix=True)
n = 0
modelV,modelI = np.empty((len(srcs),xin1.size)),np.empty((len(srcs),xin1.size))
print modelV.shape
for src in srcs:
    src.setPars()
    tmpV,tmpI = xc*0., xc*0.
    tmpV[mask2],tmpI[mask2] = src.pixeval(x0V,y0V,1./OVRS,csub=21),src.pixeval(x0I,y0I,1./OVRS,csub=21)
    tmpV, tmpI = iT.resamp(tmpV,OVRS,True), iT.resamp(tmpI,OVRS,True)
    tmpV, tmpI = convolve.convolve(tmpV,PSFs[0],False)[0], convolve.convolve(tmpI,PSFs[1],False)[0]
    print tmpV.shape, tmpV[mask].shape, tmpV[mask].ravel().shape

    modelV[n] = tmpV[mask].ravel()
    modelI[n] = tmpI[mask].ravel()
    if src.name == 'Source 2':
        modelV[n] *= -1
        modelI[n] *= -1
    n +=1
MODS = [modelV,modelI]

@pymc.deterministic
def logP(value=0.,p=pars):
    lp = 0.
    models = []
    for i in range(len(imgs)):
        if i == 0:
            dx,dy = 0,0
        else:
            dx,dy = DX,DY
        xp,yp = xc+dx,yc+dy
        image,sigma,psf = imgs[i], sigs[i], PSFs[i]
        imin,sigin,xin,yin = image[mask], sigma[mask],xp[mask2],yp[mask2]
        n = 0
        model = np.empty(((len(gals) + len(srcs)+1),imin.size))
        for gal in gals:
            gal.setPars()
            tmp = xc*0.
            tmp[mask2] = gal.pixeval(xin,yin,1./OVRS,csub=21) 
            tmp = iT.resamp(tmp,OVRS,True) 
            tmp = convolve.convolve(tmp,psf,False)[0]
            model[n] = tmp[mask].ravel()
            n +=1
        model[n:n+len(srcs)] = MODS[i]
        n += len(srcs)
        model[n] = np.ones(model[n].size)
        n+=1
        rhs = (imin/sigin) # data
        op = (model/sigin).T # model matrix
        fit, chi = optimize.nnls(op,rhs)
        model = (model.T*fit).sum(1)
        resid = (model-imin)/sigin
        lp += -0.5*(resid**2.).sum()
        models.append(model)
    return lp 


@pymc.observed
def likelihood(value=0.,lp=logP):
    return lp 

optCov = numpy.array(cov)

print len(cov), len(pars)


S = myEmcee.PTEmcee(pars+[likelihood],cov=optCov,nthreads=24,nwalkers=50,ntemps=3)
S.sample(500)
outFile = '/data/ljo31/Lens/J0837/fg_model_'+str(X)
f = open(outFile,'wb')
cPickle.dump(S.result(),f,2)
f.close()
result = S.result()
lp = result[0]
trace = numpy.array(result[1])
a1,a3 = numpy.unravel_index(lp[:,0].argmax(),lp[:,0].shape)
a2=0
for i in range(len(pars)):
    pars[i].value = trace[a1,a2,a3,i]
    print "%18s  %8.3f"%(pars[i].__name__,pars[i].value)

jj=0
for jj in range(12):
    S.p0 = trace[-1]
    S.sample(1000)

    f = open(outFile,'wb')
    cPickle.dump(S.result(),f,2)
    f.close()

    result = S.result()
    lp = result[0]

    trace = numpy.array(result[1])
    a1,a3 = numpy.unravel_index(lp[:,0].argmax(),lp[:,0].shape)
    for i in range(len(pars)):
        pars[i].value = trace[a1,a2,a3,i]
    print jj
    jj+=1


# pre-calculate most things
xin1,yin1 = xc.copy(),yc.copy()
xin2,yin2 = (xc+DX).copy(), (yc+DY).copy()
for lens in lenses:
    lens.setPars()
x0V,y0V = pylens.lens_images(lenses,srcs,[xin1,yin1],1./OVRS,getPix=True)
x0I,y0I = pylens.lens_images(lenses,srcs,[xin2,yin2],1./OVRS,getPix=True)
n = 0
modelV,modelI = np.empty((len(srcs),xin1.size)),np.empty((len(srcs),xin1.size))
for src in srcs:
    src.setPars()
    tmpV,tmpI = xc*0., xc*0.
    tmpV,tmpI = src.pixeval(x0V,y0V,1./OVRS,csub=21),src.pixeval(x0I,y0I,1./OVRS,csub=21)
    tmpV, tmpI = iT.resamp(tmpV,OVRS,True), iT.resamp(tmpI,OVRS,True)
    tmpV, tmpI = convolve.convolve(tmpV,PSFs[0],False)[0], convolve.convolve(tmpI,PSFs[1],False)[0]
    modelV[n] = tmpV.ravel()
    modelI[n] = tmpI.ravel()
    if src.name == 'Source 2':
        modelV[n] *= -1
        modelI[n] *= -1
    pl.figure()
    pl.imshow(tmpV,interpolation='nearest',origin='lower')
    pl.show()
    n +=1
MODS = [modelV,modelI]


colours = ['F555W', 'F814W']
models = []
fits = []
for i in range(len(imgs)):
    if i == 0:
        dx,dy = 0,0
    else:
        dx,dy = DX,DY
    xp,yp = xc+dx,yc+dy
    image,sigma,psf = imgs[i], sigs[i], PSFs[i]
    imin,sigin,xin,yin = image.flatten(), sigma.flatten(),xp.flatten(),yp.flatten()
    n = 0
    model = np.empty(((len(gals) + len(srcs)+1),imin.size))
    for gal in gals:
        gal.setPars()
        tmp = xc*0.
        tmp = gal.pixeval(xp,yp,1./OVRS,csub=21) 
        tmp = iT.resamp(tmp,OVRS,True) 
        tmp = convolve.convolve(tmp,psf,False)[0]
        model[n] = tmp.ravel()
        n +=1
    model[n:n+len(srcs)] = MODS[i]
    n += len(srcs)
    model[n] = np.ones(model[n].size)
    n+=1
    print n
    rhs = image[mask]/sigma[mask]
    mmodel = model.reshape((n,image.shape[0],image.shape[1]))
    mmmodel = np.empty(((len(gals) + len(srcs)+1),image[mask].size))
    for m in range(mmodel.shape[0]):
        mmmodel[m] = mmodel[m][mask]
    op = (mmmodel/sigma[mask]).T
    rhs = image[mask]/sigma[mask]
    fit, chi = optimize.nnls(op,rhs)
    components = (model.T*fit).T.reshape((n,image.shape[0],image.shape[1]))
    model = components.sum(0)
    models.append(model)
    print fit
    for j in range(3):
        pl.figure()
        pl.imshow(components[j],origin='lower',interpolation='nearest')
        pl.colorbar()
        pl.show()
    NotPlicely(image,model,sigma)
    pl.suptitle(str(colours[i]))
    pl.show()
    #pl.close('all')

print gals[0].x, srcs[0].x, srcs[1].x, lenses[0].x
