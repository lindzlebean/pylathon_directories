import numpy as np, pylab as pl, pyfits as py, cPickle
import pymc, myEmcee_blobs as myEmcee
from astLib import astCalc
from scipy.interpolate import splrep, splev,splint
from tools import solarmag
from astLib import astCalc

dat = np.loadtxt('/data/ljo31b/EELs/sizemass/re_allflux.dat')
r = dat[:,0]
f = dat[:,1:]
f = f[:,:-1]

logSigma, mu, logRe, dlogSigma, dmu, dlogRe = np.load('/data/ljo31b/EELs/esi/kinematics/FP_EELs_mu.npy').T
rho = np.load('/data/ljo31/Lens/LensParams/ReMu_covariances.npy')[:,3]

sz = np.load('/data/ljo31/Lens/LensParams/SourceRedshiftsUpdated_1.00_lens_vdfit.npy')[()]
names = sz.keys()
names.sort()

scales = np.array([astCalc.da(sz[name][0])*1e3*np.pi/180./3600. for name in names])
Re=10**logRe
dRe = dlogRe*Re
mag = mu - 2.5*np.log10(2.*np.pi*Re**2./scales**2.)

bands = np.load('/data/ljo31/Lens/LensParams/HSTBands.npy')[()]
logI,dlogI = mu*0,mu*0
logL = mu*0
logLR = mu*0.

for ii in range(len(names)):
    band = bands[names[ii]]
    logL[ii] = solarmag.mag_to_logL(mag[ii],band+'_ACS',sz[names[ii]][0]) - 8.
    logLR[ii] =  np.log10(2.*np.pi*Re[ii]**2.)
    logI[ii] =  logL[ii] - logLR[ii]

dlogI = 0.4*dmu

# cut J2228?
logSigma,logRe,mu,mag,logI = logSigma[:-1],logRe[:-1],mu[:-1],mag[:-1],logI[:-1]
dlogSigma,dlogRe,dmu,dmag,dlogI = dlogSigma[:-1],dlogRe[:-1],dmu[:-1],dmu[:-1],dlogI[:-1]
scales = scales[:-1]
Re = Re[:-1]
#logSigma,logRe,mu,mag = np.delete(logSigma,9),np.delete(logRe,9),np.delete(mu,9),np.delete(mag,9)
#dlogSigma,dlogRe,dmu,dmag = np.delete(dlogSigma,9),np.delete(dlogRe,9),np.delete(dmu,9),np.delete(dmu,9)
#scales = np.delete(scales,9)
#Re = np.delete(Re,9)

fluxes = Re*0.
for i in range(f.shape[1]):
    logR = np.log10(r*0.05*scales[i])
    nmod = splrep(logR,f[:,i])
    nnorm = splint(logR[0],logR[-1],nmod)
    model = splrep(r*0.05*scales[i], f[:,i]/nnorm)
    fluxes[i] = splev(Re[i],model)

pars, cov = [], []
alpha = pymc.Uniform('alpha',-10.,10 )
beta = pymc.Uniform('beta',-5,5 )
gamma = pymc.Uniform('gamma',-20.,20. )
mux = pymc.Uniform('mu x',-0.5,1.0 )
muy = pymc.Uniform('mu y',-10.,10. )
taux = pymc.Uniform('tau x',0,1,0.1 )
tauy = pymc.Uniform('tau y',0,6,1.0 )
sigma = pymc.Uniform('sigma',0,1 )
pars = [alpha,beta,gamma,mux,muy,taux,tauy,sigma]
cov += [1.,1.,1.,0.5,0.5,0.05,0.1,0.1]
optCov = np.array(cov)


@pymc.deterministic
def logP(value=0.,p=pars):
    a,b,g = alpha.value, beta.value, gamma.value
    logrfunc = a*logSigma + b*logI + g
    sigma2 = sigma.value**2. + dlogRe**2.
    arg = (logRe -logrfunc)**2./sigma2 
    s_arg = (logSigma - mux.value)**2. / (dlogSigma**2. + taux.value**2.)
    m_arg = (logI-muy.value)**2. / (dlogI**2. + tauy.value**2.)
    s_norm = (2.*np.pi*(dlogSigma**2. + taux.value**2.))**0.5
    m_norm = (2.*np.pi*(dmu**2. + tauy.value**2.))**0.5
    norm = (2.*np.pi*sigma2)**0.5
    prob = np.log(3.*fluxes) - np.log(norm) - 0.5*arg - 0.5*s_arg - 0.5*m_arg - np.log(s_norm) - np.log(m_norm)
    lp = prob.sum()
    return lp

@pymc.observed
def likelihood(value=0.,lp=logP):
    return lp

S = myEmcee.Emcee(pars+[likelihood],cov=optCov,nthreads=1,nwalkers=80)
S.sample(5000)
outFile = '/data/ljo31b/EELs/FP/inference/FP_intrinsic_2src_logI'
f = open(outFile,'wb')
cPickle.dump(S.result(),f,2)
f.close()
result = S.result()
result = np.load(outFile)
lp,trace,dic,_ = result
a1,a2 = np.unravel_index(lp.argmax(),lp.shape)
ftrace=trace.reshape((trace.shape[0]*trace.shape[1],trace.shape[2]))
for i in range(len(pars)):
    pars[i].value = np.percentile(ftrace[1000:,i],50,axis=0)
    print "%18s  %8.5f"%(pars[i].__name__,pars[i].value)


a,b,alpha,mux,muy,taux,tauy,sigma = pars[0].value, pars[1].value,pars[2].value, pars[3].value,pars[4].value, pars[5].value, pars[6].value,pars[7].value
da, db = a - np.percentile(dic['alpha'][-300:].ravel(),16), b -np.percentile(dic['beta'][-300:].ravel(),16)
gamma16,gamma84 = np.percentile(dic['gamma'][-300:].ravel(),16),np.percentile(dic['gamma'][-300:].ravel(),84)
dgamma = np.mean((gamma-gamma16,gamma84-gamma))
print dgamma, sigma


Zline = np.linspace(min(logRe),max(logRe),10)
pl.plot(Zline,Zline,color='Crimson',label='observed')
pl.fill_between(Zline,Zline,Zline+sigma,color='LightPink',alpha=0.5)
pl.fill_between(Zline,Zline,Zline-sigma,color='LightPink',alpha=0.5)
