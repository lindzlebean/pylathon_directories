import numpy as np, pylab as pl, pyfits as py
from scipy.interpolate import splrep, splint, splev
import pymc
import myEmcee_blobs as myEmcee
from numpy import cos, sin, tan
import cPickle

T = 4e9
logT = np.log10(T)
table = py.open('/data/ljo31/Lens/LensParams/Phot_1src.fits')[1].data
### load up BC03 tables and build interpolators, so we can change the age quickly and update the ML estimate
age_cols,vi, vk = np.loadtxt('/data/mauger/STELLARPOP/chabrier/bc2003_lr_m62_chab_ssp.2color',unpack=True,usecols=(0,5,7))
age_mls, ml_b, ml_v = np.loadtxt('/data/mauger/STELLARPOP/chabrier/bc2003_lr_m62_chab_ssp.4color',unpack=True,usecols=(0,4,5))
vimod, vkmod = splrep(age_cols, vi), splrep(age_cols, vk)
mlbmod, mlvmod = splrep(age_mls,ml_b), splrep(age_mls,ml_v)
mlb, mlv = splev(logT,mlbmod), splev(logT,mlvmod)
lumb, lumv, Re, dlumb, dlumv, dRe, name = table['lum b'], table['lum v'], table['Re v'], table['lum b hi'], table['lum v hi'], table['Re v hi'], table['name']
ii=np.isfinite(lumb)
lumb,lumv,Re,dlumb,dlumv,dRe,name = lumb[ii],lumv[ii],Re[ii],dlumb[ii],dlumv[ii],dRe[ii],name[ii]
logMb, logMv = np.log10(mlb) + lumb, np.log10(mlv) + lumv
logRe = np.log10(Re)

# set up fit parameters. Now we're fitting the B band -- and skipping J0837 for now
x,y = logMb[1:], logRe[1:]
sxx, syy = dlumb[1:], dRe[1:]/Re[1:]
sxy, syx = y*0., x*0.
sxx2, syy2 = sxx**2., syy**2.

#pl.figure()
#pl.scatter(x,y)
#pl.errorbar(x,y,xerr=sxx,yerr=syy,fmt='o')

# fit!!!
pars, cov = [], []
pars.append(pymc.Uniform('theta',-np.pi/2., np.pi/2.,value=0.5 ))
pars.append(pymc.Uniform('b',-20,-5,value=-10 ))
pars.append(pymc.Uniform('scatter',0,0.5,value=0.001))
cov += [0.1,0.5,0.05]
optCov = np.array(cov)

@pymc.deterministic
def logP(value=0.,p=pars):
    lp=0.
    theta,b,scatter = pars[0].value, pars[1].value,pars[2].value
    st,ct = sin(theta), cos(theta)
    Delta = y*ct - x*st - b*ct
    Sigma = sxx2*st**2. + syy2*ct**2. -st*ct*(sxy+syx) + scatter**2.
    pdf = -0.5*Delta**2./Sigma - 0.5*np.log(Sigma)
    lp = pdf.sum()
    return lp

@pymc.observed
def likelihood(value=0.,lp=logP):
    return lp

S = myEmcee.Emcee(pars+[likelihood],cov=optCov,nthreads=1,nwalkers=20)
S.sample(10000)
outFile = '/data/ljo31/Lens/Analysis/sizemass'
f = open(outFile,'wb')
cPickle.dump(S.result(),f,2)
f.close()
result = S.result()
lp,trace,dic,_ = result
a1,a2 = np.unravel_index(lp.argmax(),lp.shape)
for i in range(len(pars)):
    pars[i].value = trace[a1,a2,i]
    print "%18s  %8.5f"%(pars[i].__name__,pars[i].value)

for i in range(3):
    pl.figure()
    pl.plot(trace[:,:,i])



theta,b,scatter = pars[0].value, pars[1].value,pars[2].value
m = tan(theta)
xfit = np.linspace(10,12,20)
yfit = m*xfit + b


burnin=100
f = trace[burnin:].reshape((trace[burnin:].shape[0]*trace[burnin:].shape[1],trace[burnin:].shape[2]))
fits=np.zeros((len(f),xfit.size))
for j in range(0,len(f)):
    theta,b,scatter = f[j]
    m=tan(theta)
    fits[j] = m*xfit+b
    
lo,med,up = yfit*0.,yfit*0.,yfit*0.
for j in range(xfit.size):
    lo[j],med[j],up[j] = np.percentile(fits[:,j],[16,50,84],axis=0)

los,meds,ups = np.percentile(f,[16,50,84],axis=0)
los,ups=meds-los,ups-meds

pl.figure()
pl.plot(xfit,yfit,'k-')
pl.fill_between(xfit,yfit,lo,color='Gainsboro')
pl.fill_between(xfit,yfit,up,color='Gainsboro')
pl.scatter(x,y)
pl.errorbar(x,y,xerr=sxx,yerr=syy,fmt='o')
pl.text(10.1,1.5,r'$\log(R_e) = \alpha\log(M) + \beta$')
pl.text(10.1,1.3,r'$\alpha = $'+'%.2f'%tan(pars[0].value)+'$\pm$'+'%.2f'%tan(los[0]))
pl.text(10.1,1.1,r'$\beta = $'+'%.2f'%pars[1].value+'$\pm$'+'%.2f'%los[1])
pl.text(10.1,0.9,r'$\sigma = $'+'%.5f'%pars[2].value+'$\pm$'+'%.2f'%los[2])
pl.axis([10,12,-0.5,2])
pl.xlabel(r'$\log(M/M_{\odot})$')
pl.ylabel(r'$\log(R_e/kpc)$')
#pl.plot(xfit,yfit,'k-',lw=2)
pl.figure()
for theta,b,scatter in f[np.random.randint(len(f), size=100)]:
    m=tan(theta)
    pl.plot(xfit,m*xfit+b,color='k',alpha=0.1)
pl.scatter(x,y)
pl.errorbar(x,y,xerr=sxx,yerr=syy,fmt='o')
pl.axis([10,12,-0.5,2])
pl.xlabel(r'$\log(M/M_{\odot})$')
pl.ylabel(r'$\log(R_e/kpc)$')

yfit=tan(meds[0])*xfit+meds[1]
pl.figure()
pl.plot(xfit,yfit,'k-')
pl.fill_between(xfit,yfit,lo,color='Gainsboro')
pl.fill_between(xfit,yfit,up,color='Gainsboro')
pl.scatter(x,y)
pl.errorbar(x,y,xerr=sxx,yerr=syy,fmt='o')
pl.text(10.1,1.5,r'$\log(R_e) = \alpha\log(M) + \beta$')
pl.text(10.1,1.3,r'$\alpha = $'+'%.2f'%tan(meds[0])+'$\pm$'+'%.2f'%tan(los[0]))
pl.text(10.1,1.1,r'$\beta = $'+'%.2f'%meds[1]+'$\pm$'+'%.2f'%los[1])
pl.text(10.1,0.9,r'$\sigma = $'+'%.3f'%meds[2]+'$\pm$'+'%.2f'%los[2])
pl.axis([10,12,-0.5,2])
pl.xlabel(r'$\log(M/M_{\odot})$')
pl.ylabel(r'$\log(R_e/kpc)$')
