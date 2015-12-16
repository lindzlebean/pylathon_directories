import cPickle,numpy,pyfits
import pymc
from pylens import *
from imageSim import SBModels,convolve
import indexTricks as iT
from SampleOpt import AMAOpt
import pylab as pl
import numpy as np
import lensModel2

# try basicmodel4 with a load of different position angles for source 1
'''
X = 0 - one source component, one galaxy componnet. basicmodel2a
X = 1 - basicmodel2c. With two source components
X = 2 - basicmodel2e. With source 2 starting in a better position
X = 3 - basicmodel2f, with a pa = 80, q = 0.65 for source 2
X = 4 - basicmodel2g, with pa = 80, q = 0.75 for source 1
X = 5 - basicmodel2h, with source positions fixed. Based on basicmodelc.
X = 6 - basicmodel2h2 - rotated source 1
X = 7 - basicmodel2h3 - roated source 2 as well
X = 8 - basicmodel2h4 - focussing on re and n BEST SO FAR!!!
X = 10 - basicmodel2h4_alluniform
X = 11 - basicmodel2i
X = 12 - basicmodel2h4_alluniform_srcpas -  with pas of sources rotated by 90 degrees in case they want to be elliptical!
X = 13 trying to reprodice X = 8...
X=14
X = 15 - with X=8, pa = 140
X = 16 - putting a load of parameters in by hand
X = 17 - same as X=4 because this had the best starting logp, but this time adding in shear
X = 18 - as 17, but putting in re = 0.6 for source 1

'''

# plot things
def NotPlicely(image,im,sigma):
    ext = [0,image.shape[0],0,image.shape[1]]
    #vmin,vmax = numpy.amin(image), numpy.amax(image)
    pl.figure()
    pl.subplot(221)
    pl.imshow(image,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',aspect='auto') #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('data')
    pl.subplot(222)
    pl.imshow(im,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',aspect='auto') #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('model')
    pl.subplot(223)
    pl.imshow(image-im,origin='lower',interpolation='nearest',extent=ext,vmin=-0.25,vmax=0.25,cmap='afmhot',aspect='auto')
    pl.colorbar()
    pl.title('data-model')
    pl.subplot(224)
    pl.imshow((image-im)/sigma,origin='lower',interpolation='nearest',extent=ext,vmin=-3,vmax=3,cmap='afmhot',aspect='auto')
    pl.title('signal-to-noise residuals')
    pl.colorbar()
    #pl.suptitle(str(V))
    #pl.savefig('/data/ljo31/Lens/TeXstuff/plotrun'+str(X)+'.png')


img1 = pyfits.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F606W_sci_cutout.fits')[0].data.copy()
sig1 = pyfits.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F606W_noisemap.fits')[0].data.copy()
psf1 = pyfits.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F606W_psf.fits')[0].data.copy()
psf1 = psf1[15:-15,15:-15]
psf1 /= psf1.sum()

img2 = pyfits.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F814W_sci_cutout.fits')[0].data.copy()
sig2 = pyfits.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F814W_noisemap.fits')[0].data.copy()
psf2 = pyfits.open('/data/ljo31/Lens/J1347/SDSSJ1347-0101_F814W_psf_#2.fits')[0].data.copy()
psf2 = psf2[15:-15,15:-16]
psf2 /= psf2.sum()


imgs = [img1,img2]
sigs = [sig1,sig2]
psfs = [psf1,psf2]

OVRS = 4
PSFs = []
yc,xc = iT.overSample(img1.shape,OVRS)
yc,xc = yc,xc
for i in range(len(imgs)):
    psf = psfs[i]
    image = imgs[i]
    psf /= psf.sum()
    psf = convolve.convolve(image,psf)[1]
    PSFs.append(psf)


det = np.load('/data/ljo31/Lens/J1347/det19.npy')[()]

srcs = []
gals = []
lenses = []
coeff=[]
g1,g2,l1,s1,s2,sh = {},{},{},{},{},{}


for name in det.keys():
    s = det[name]
    coeff.append(s[-1])
    if name[:8] == 'Source 1':
        s1[name[9:]] = s[-1]
    elif name[:8] == 'Source 2':
        s2[name[9:]] = s[-1]
    elif name[:6] == 'Lens 1':
        l1[name[7:]] = s[-1]
    elif name[:8] == 'Galaxy 1':
        g1[name[9:]] = s[-1]
    elif name[:8] == 'Galaxy 2':
        g2[name[9:]] = s[-1]
    elif name[:8] == 'extShear':
        if len(name)<9:
            sh['b'] = s[-1]
        elif name == 'extShear PA':
            sh['pa'] = s[-1]
    


s1['x'],s2['x'] = 34.3,34.3
s1['y'],s2['y'] = 36.4, 36.4
#s1['x'] = s2['x'].copy()
#s1['y'] = s2['y'].copy()
g2['x'] = g1['x'].copy()
g2['y'] = g1['y'].copy()
srcs.append(SBModels.Sersic('Source 1',s1))
srcs.append(SBModels.Sersic('Source 2',s2))
gals.append(SBModels.Sersic('Galaxy 1',g1))
#gals.append(SBModels.Sersic('Galaxy 2',g2))
lenses.append(MassModels.PowerLaw('Lens 1',l1))
sh['x'] = lenses[0].pars['x']
sh['y'] = lenses[0].pars['y']
lenses.append(MassModels.ExtShear('shear',sh))

lp = 0.
for i in range(len(imgs)):
    if i == 0:
        x0,y0 = 0,0
    else:
        x0 = det['xoffset'][-1]
        y0 = det['yoffset'][-1]
        #print x0,y0
    image = imgs[i]
    sigma = sigs[i]
    psf = PSFs[i]
    lp += lensModel.lensFit(None,image,sigma,gals,lenses,srcs,xc+x0,yc+y0,OVRS,
                                verbose=False,psf=psf,csub=1)
print 'lp = ', lp
   


ims = []
models = []
for i in range(len(imgs)):
    image = imgs[i]
    sigma = sigs[i]
    psf = PSFs[i]
    if i == 0:
        x0,y0 = 0,0
    else:
        x0,y0 = det['xoffset'][-1], det['yoffset'][-1] # xoffset, yoffset #
        print x0,y0
    im = lensModel.lensFit(coeff,image,sigma,gals,lenses,srcs,xc+x0,yc+y0,OVRS,psf=psf,verbose=True) # return loglikelihood
    print im
    im = lensModel.lensFit(coeff,image,sigma,gals,lenses,srcs,xc+x0,yc+y0,OVRS,noResid=True,psf=psf,verbose=True) # return model
    model = lensModel.lensFit(coeff,image,sigma,gals,lenses,srcs,xc+x0,yc+y0,OVRS,noResid=True,psf=psf,verbose=True,getModel=True,showAmps=True) # return the model decomposed into the separate galaxy and source components
    ims.append(im)
    models.append(model)

colours = ['F606W', 'F814W']
for i in range(len(imgs)):
    image = imgs[i]
    im = ims[i]
    model = models[i]
    sigma = sigs[i]
    #pyfits.PrimaryHDU(model).writeto('/data/ljo31/Lens/J1347/components_uniform'+str(colours[i])+str(X)+'.fits',clobber=True)
    #pyfits.PrimaryHDU(im).writeto('/data/ljo31/Lens/J1347/model_uniform'+str(colours[i])+str(X)+'.fits',clobber=True)
    #pyfits.PrimaryHDU(image-im).writeto('/data/ljo31/Lens/J1347/resid_uniform'+str(colours[i])+str(X)+'.fits',clobber=True)
    #f = open('/data/ljo31/Lens/J1347/coeff'+str(X),'wb')
    #cPickle.dump(coeff,f,2)
    #f.close()
    NotPlicely(image,im,sigma)
    pl.suptitle(str(colours[i]))


#numpy.save('/data/ljo31/Lens/J1606/trace'+str(Y), trace)
#numpy.save('/data/ljo31/Lens/J1606/logP'+str(Y), logp)
'''
for key in det.keys():
    print key, '%.1f'%det[key][-1]
print 'max lnL is ', max(logp)

print det['xoffset'], det['yoffset']
np.save('/data/ljo31/Lens/J1347/det'+str(X),det)

#print 'x & y & n & re & q & pa \\'
print '&','&', '%.1f'%det['Source 1 n'][-1], '&', '%.1f'%det['Source 1 re'][-1], '&', '%.1f'%det['Source 1 q'][-1], '&', '%.1f'%det['Source 1 pa'][-1], '\\'
print '%.1f'%det['Source 2 x'][-1], '&', '%.1f'%det['Source 2 y'][-1],' &', '%.1f'%det['Source 2 n'][-1], '&', '%.1f'%det['Source 2 re'][-1], '&', '%.1f'%det['Source 2 q'][-1], '&', '%.1f'%det['Source 2 pa'][-1], '\\'
print '%.1f'%det['Galaxy 1 x'][-1], '&', '%.1f'%det['Galaxy 1 y'][-1], '&', '%.1f'%det['Galaxy 1 n'][-1], '&', '%.1f'%det['Galaxy 1 re'][-1], '&', '%.1f'%det['Galaxy 1 q'][-1], '&', '%.1f'%det['Galaxy 1 pa'][-1], '\\'
print '%.1f'%det['Lens 1 x'][-1], '&', '%.1f'%det['Lens 1 y'][-1], '&', '%.1f'%det['Lens 1 eta'][-1], '&', '%.1f'%det['Lens 1 b'][-1], '&', '%.1f'%det['Lens 1 q'][-1], '&', '%.1f'%det['Lens 1 pa'][-1], '\\'
'''
fits = []
for i in range(len(imgs)):
    image = imgs[i]
    sigma = sigs[i]
    psf = PSFs[i]
    if i == 0:
        x0,y0 = 0,0
    else:
        x0,y0 = det['xoffset'][-1], det['yoffset'][-1] # xoffset, yoffset #
        print x0,y0
    fit = lensModel2.lensFit(coeff,image,sigma,gals,lenses,srcs,xc+x0,yc+y0,OVRS,noResid=True,psf=psf,verbose=True,getModel=True,showAmps=True) # return the model decomposed into the separate galaxy and source components
    fits.append(fit)

print fits
