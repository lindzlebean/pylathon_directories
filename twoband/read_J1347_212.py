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

#this possibly needs ptemcee?

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

img1 = py.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F606W_sci_cutout_huge.fits')[0].data.copy()[25:-25,25:-25]
sig1 = py.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F606W_noisemap_huge.fits')[0].data.copy()[25:-25,25:-25]
psf1 = py.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F606W_psf.fits')[0].data.copy()
psf1 = psf1[15:-15,15:-15]
psf1 /= psf1.sum()
img2 = py.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F814W_sci_cutout_huge.fits')[0].data.copy()[25:-25,25:-25]
sig2 = py.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F814W_noisemap_huge.fits')[0].data.copy()[25:-25,25:-25]
psf2 = py.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F814W_psf_#2.fits')[0].data.copy()
psf2 = psf2[15:-15,15:-16]
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

result = np.load('/data/ljo31/Lens/J1347/twoband_212_2_ctd')
lp,trace,dic,_= result
a2=0
a1,a3 = numpy.unravel_index(lp[:,0].argmax(),lp[:,0].shape)

OVRS = 3
yc,xc = iT.overSample(img1.shape,OVRS)
yo,xo = iT.overSample(img1.shape,1)
yc,yo=yc-62,yo-62
xc,xo=xc-64,xo-64
mask = py.open('/data/ljo31/Lens/J1347/mask_huge.fits')[0].data[25:-25,25:-25] + py.open('/data/ljo31/Lens/J1347/mask_extra.fits')[0].data [25:-25,25:-25]
tck = RectBivariateSpline(yo[:,0],xo[0],mask)
mask2 = tck.ev(xc,yc)
mask2[mask2<0.5] = 0
mask2[mask2>0.5] = 1
mask2 = mask2==0
mask = mask==0

lresult = np.load('/data/ljo31/Lens/LensModels/J1347_112')
llp,ltrace,ldic,_= lresult
la2=0
la1,la3 = numpy.unravel_index(llp[:,0].argmax(),llp[:,0].shape)


pars = []
cov = []

gals = []
name = 'Galaxy 1'
p = {}
for key in 'x','y','q','pa','re','n':
    p[key] = dic[name+' '+key][a1,a2,a3]
gals.append(SBModels.Sersic(name,p))


# lensing is fixed except for the power law slope
lenses = []
p = {}
for key in 'x','y','q','pa','b','eta':
    p[key] = dic['Lens 1 '+key][a1,a2,a3]
lenses.append(MassModels.PowerLaw('Lens 1',p))

p = {}
p['x'] = lenses[0].pars['x']
p['y'] = lenses[0].pars['y']
p['b'] = dic['extShear'][a1,a2,a3]
p['pa'] = dic['extShear PA'][a1,a2,a3]
lenses.append(MassModels.ExtShear('shear',p))

srcs = []
for name in ['Source 2','Source 1']:
    p = {}
    for key in 'q','re','n','pa':
        p[key] = dic[name+' '+key][a1,a2,a3]
    for key in 'x','y': 
        if name+' '+key in dic.keys():
            p[key] = dic[name+' '+key][a1,a2,a3] #+ lenses[0].pars[key]
        else:
            p[key] = srcs[0].pars[key]
    srcs.append(SBBModels.Sersic(name,p))


colours = ['F555W', 'F814W']
models = []
fits = []
for i in range(len(imgs)):
    if i == 0:
        dx,dy = 0,0
    else:
        dx = dic['xoffset'][a1,a2,a3]
        dy = dic['yoffset'][a1,a2,a3]
    xp,yp = xc+dx,yc+dy
    xop,yop = xo+dy,yo+dy
    image = imgs[i]
    sigma = sigs[i]
    psf = PSFs[i]
    imin,sigin,xin,yin = image.flatten(), sigma.flatten(),xp.flatten(),yp.flatten()
    n = 0
    model = np.empty(((len(gals) + len(srcs)+1),imin.size))
    for gal in gals:
        gal.setPars()
        tmp = xc*0.
        tmp = gal.pixeval(xp,yp,1./OVRS,csub=21) # evaulate on the oversampled grid. OVRS = number of new pixels per old pixel.
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
        tmp = src.pixeval(x0,y0,1./OVRS,csub=21)
        tmp = iT.resamp(tmp,OVRS,True)
        tmp = convolve.convolve(tmp,psf,False)[0]
        model[n] = tmp.ravel()
        n +=1
    model[n] = np.ones(model[n].shape)
    n+=1
    rhs = image[mask]/sigma[mask]
    print model.shape, model.size
    mmodel = model.reshape((n,image.shape[0],image.shape[1]))
    mmmodel = np.empty(((len(gals) + len(srcs)+1),image[mask].size))
    for m in range(mmodel.shape[0]):
        print mmodel[m].shape
        mmmodel[m] = mmodel[m][mask]
    op = (mmmodel/sigma[mask]).T
    rhs = image[mask]/sigma[mask]
    fit, chi = optimize.nnls(op,rhs)
    components = (model.T*fit).T.reshape((n,image.shape[0],image.shape[1]))
    model = components.sum(0)
    models.append(model)
    NotPlicely(image,model,sigma)
    pl.suptitle(str(colours[i]))
    pl.show()
    #print fit

'''for i in range(components.shape[0]-1):
    pl.figure()
    pl.imshow(components[i],interpolation='nearest',origin='lower')
    pl.colorbar()

pl.figure()
pl.plot(lp[:,0])'''

ldic = np.load('/data/ljo31/Lens/J1347/twoband_212_2')[2]


for key in ['Source 1 re', 'Source 1 n', 'Source 2 re','Source 2 n','Galaxy 1 re', 'Galaxy 1 n']:
    pl.figure()
    pl.subplot(211)
    pl.hist(dic[key][:,0].ravel(),30,normed=True,histtype='stepfilled',alpha=0.5)
    pl.hist(ldic[key][:,0].ravel(),30,normed=True,histtype='stepfilled',alpha=0.5)
    pl.subplot(212)
    pl.plot(dic[key][:,0])
    pl.suptitle(key)

