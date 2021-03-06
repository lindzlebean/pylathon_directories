import numpy as np, pylab as pl, pyfits as py
import pymc
import myEmcee_blobs as myEmcee
import cPickle
from tools import solarmag
from stellarpop import distances
from SampleOpt import AMAOpt
from astLib import astCalc
from scipy.interpolate import splrep, splev,splint

dat = np.loadtxt('/data/ljo31b/EELs/sizemass/re_allflux.dat')
r = dat[:,0]
f = dat[:,1:]
f2 = np.loadtxt('/data/ljo31b/EELs/sizemass/flux_FP.dat')

# what happens if we say there's no DM in these systems? -- alpha = 1.4
# the fact that even with no DM we don't get the virial plane means there must be further stellar population and structural trends?

fp = np.load('/data/ljo31b/EELs/esi/kinematics/inference/results_NEW_0.30_source_indous_vdfit_jul2016_J2228.npy')
l,m,u = fp
d = np.mean((l,u),axis=0)
dvl,dvs,dsigmal,dsigmas = d.T
vl,vs,sigmal,sigmas = m.T
dsigmas = sigmas*0.05
dsigmas[-2:] = sigmas[-2:]*0.1
sigmas /= 200.
sigmal /= 200.
dsigmas /= 200.
dsigmal /= 200.
# remove J1248 as we don't have photometry
sz = np.load('/data/ljo31/Lens/LensParams/SourceRedshiftsUpdated_1.00_lens_vdfit.npy')[()]
lz = np.load('/data/ljo31/Lens/LensParams/LensRedshiftsUpdated_1.00_lens_vdfit.npy')[()]

phot = py.open('/data/ljo31/Lens/LensParams/Phot_2src_huge_new_new.fits')[1].data
names = phot['name']

re,rel,reu = phot['Re v'], phot['Re v lo'], phot['Re v hi']
dre = np.mean((rel,reu),axis=0)
mu,mul,muu = phot['mu v'], phot['mu v lo'], phot['mu v hi']
dmu = np.mean((mul,muu),axis=0)

sigs = np.load('/data/ljo31/Lens/LensParams/ReMu_covariances.npy')
rho = sigs[:,3]

scales = np.array([astCalc.da(sz[name][0])*1e3*np.pi/180./3600. for name in names])

B,Bup,Blo,V,Vup,Vlo = np.load('/data/ljo31/Lens/LensParams/B_V_redshift0_model_marginalised.npy').T
logI = V-9
dlogI = np.mean((Vup-V,V-Vlo),0)

logI = np.load('/data/ljo31/Lens/LensParams/V_redshift0_model.npy')

logI -= 9.0

fluxes = re*0.
for i in range(f.shape[1]):
    logR = np.log10(r*0.05*scales[i])
    nmod = splrep(logR,f[:,i])
    nnorm = splint(logR[0],logR[-1],nmod)
    model = splrep(r*0.05*scales[i], f[:,i]/nnorm)
    fluxes[i] = splev(re[i],model)
    #pl.figure()
    #pl.plot(r,f[:,i]/nnorm)
    #pl.show()

xx,yy,zz = np.log10(sigmas), logI, np.log10(re)
xo,yo,zo = xx.copy(),yy.copy(),zz.copy()
dxx,dyy,dzz = dsigmas/sigmas/np.log(10.), dlogI, dre/re/np.log(10.)
dxo,dyo,dzo = dxx.copy(),dyy.copy(),dzz.copy()
sxx,syy,szz = dxx**2.,dyy**2.,dzz**2.
syz,szy = 0.,0.
sxy,syx,sxz,szx = 0,0,0,0
syz,szy=0,0
syz,szy = rho*dyy*dzz,rho*dyy*dzz
syz,szy = np.zeros(dyy.size), np.zeros(dyy.size)#rho*dyy*dzz,rho*dyy*dzz

print fluxes.shape, yy.shape, xx.shape
I=-3 # J1606
names = np.delete(names,I)
yy,zz,syy,szz = np.delete(yy,I),np.delete(zz,I),np.delete(syy,I),np.delete(szz,I)

fluxes = np.delete(fluxes, I, 0)
print fluxes.shape, xx.shape, yy.shape, zz.shape


for ii in range(names.size):
    print names[ii],'&','%.2f'%(10**zz[ii]) , '$\pm$', '%.2f'%(dzz[ii]*zz[ii]*np.log(10.)), '&', '%.2f'%(10**xx[ii] * 200.), '$\pm$', '%.2f'%(dxx[ii]*10**xx[ii]*np.log(10.)*200.), '&', '%.2f'%(9.+yy[ii]),'$\pm$', '%.2f'%dyy[ii]

pars, cov = [], []
alpha = pymc.Uniform('alpha',-10.,10 )
beta = pymc.Uniform('beta',-5,5 )
gamma = pymc.Uniform('gamma',-20.,20. )
mux = pymc.Uniform('mu x',-5,5.0 )
muy = pymc.Uniform('mu y',-10.,10. )
taux = pymc.Uniform('tau x',0,1,0.1 )
tauy = pymc.Uniform('tau y',0,6,1.0 )
logsigma = pymc.Uniform('log sigma',-3,-0.5 )
pars = [alpha,beta,gamma,mux,muy,taux,tauy,logsigma]
cov += [1.,1.,1.,0.5,0.5,0.05,0.1,0.1]
optCov = np.array(cov)


@pymc.deterministic
def logP(value=0.,p=pars):
    a,b,g = alpha.value, beta.value, gamma.value
    s = 10**logsigma.value
    logrfunc = a*xx + b*yy + g
    sigma2 = s**2. + szz
    arg = (zz -logrfunc)**2./sigma2 
    s_arg = (xx - mux.value)**2. / (sxx + taux.value**2.)
    m_arg = (yy-muy.value)**2. / (syy + tauy.value**2.)
    s_norm = (2.*np.pi*(sxx + taux.value**2.))**0.5
    m_norm = (2.*np.pi*(syy + tauy.value**2.))**0.5
    norm = (2.*np.pi*sigma2)**0.5
    prob =  - np.log(norm) - 0.5*arg - 0.5*s_arg - 0.5*m_arg - np.log(s_norm) - np.log(m_norm)
    lp = prob.sum()
    return lp

# np.log((1.+2.*b)*fluxes)



@pymc.observed
def likelihood(value=0.,lp=logP):
    return lp

# optimise first!

SS = AMAOpt(pars,[likelihood],[logP],cov=cov)
SS.sample(4000)
lp,trace,det = SS.result()
#pl.figure()
#pl.plot(lp)
#pl.show() 
print 'results from optimisation:'
for i in range(len(pars)):
    pars[i].value = trace[-1,i]
    print "%18s  %8.3f"%(pars[i].__name__,pars[i].value)

print 'new!'
#S = myEmcee.Emcee(pars+[likelihood],cov=optCov/5.,nthreads=8,nwalkers=28)
#S.sample(3000)
outFile = '/data/ljo31b/EELs/FP/inference/FP_logI_CHECK_NEW_1_INTRINSIC' # NEW referring to nfit=6
#f = open(outFile,'wb')
#cPickle.dump(S.result(),f,2)
#f.close()
#result = S.result()
result = np.load(outFile)
lp,trace,dic,_ = result
a1,a2 = np.unravel_index(lp.argmax(),lp.shape)
for i in range(len(pars)):
    pars[i].value = trace[a1,a2,i]#np.median(trace[2000:,:,i])
    print "%18s  %8.5f"%(pars[i].__name__,pars[i].value)

pl.figure()
pl.plot(lp[200:])

a,b,alpha,mux,muy,taux,tauy,logsigma = pars[0].value, pars[1].value,pars[2].value, pars[3].value,pars[4].value, pars[5].value, pars[6].value,pars[7].value
sigma = 10**logsigma

dalpha = np.percentile(dic['alpha'][2000:].ravel(),84)-alpha

yerr = szz**0.5
xerr = (a**2.*sxx + b**2*syy)**0.5
pl.figure()
 
print sigma, 10**sigma

Zline = np.linspace(min(zz)-0.5,max(zz)+0.5,10)
pl.plot(Zline,Zline,color='k')
pl.fill_between(Zline,Zline,Zline+10**-1.31,color='LightGray')
pl.fill_between(Zline,Zline,Zline-10**-1.31,color='LightGray')

pl.scatter(a*xx+b*yy+alpha,zz,color='k')
pl.errorbar(a*xx+b*yy+alpha,zz,xerr=xerr,yerr=yerr,color='k',fmt='o')
#pl.scatter(a*xo[-1]+b*yo[-1]+alpha,zo[-1],color='r',s=50)
#pl.scatter(a*xo[-2]+b*yo[-2]+alpha,zo[-2],color='r',s=50)

#pl.figtext(0.2,0.8,'$a = '+'%.2f'%a+'\pm'+'%.2f'%da+'$')
#pl.figtext(0.2,0.75,'$b = '+'%.2f'%b+'\pm'+'%.2f'%db+'$')
pl.ylabel(r'log r$_e$')
pl.xlabel('%.2f'%a+'log$\sigma$ '+'-'+'%.2f'%abs(b)+'log I$_e$'+'+'+'%.2f'%alpha)

#pl.savefig('/data/ljo31b/EELs/esi/TeX/eelsFPmu.pdf')
#pl.axis([0,1.1,0,1.1])

# also a face-on view of the plane!
# plot the face-on projection
xerr = (a**2 * sxx + b**2 * syy + (a**2+b**2)*szz)**0.5
yerr = (b**2*sxx + a**2 * syy)**0.5


pl.figure()
pl.scatter(a*xx + b*yy + (a**2 + b**2)**0.5 * zz, -b*xx + a*yy, color='k')
pl.errorbar(a*xx + b*yy + (a**2 + b**2)**0.5 * zz, -b*xx + a*yy, xerr=xerr, yerr=yerr,color='k',fmt='o')
pl.xlabel('%.2f'%a+r'log$\sigma$ '+'%.2f'%b+r'log I$_e$ + '+'%.2f'%(np.sqrt(a**2.+b**2.))+r'log r$_e$')
pl.ylabel('%.2f'%(-1*b)+r'log$\sigma$ + '+'%.2f'%(a)+r'log I$_e$')
#pl.axis([-0.6,2.0,0,2.2])

# a second side-on projection
xerr = (szz + b**2 * syy)**0.5
yerr = (sxx)**0.5

pl.figure()
pl.plot(a*Zline+alpha,Zline,color='k')
pl.fill_between(a*Zline+alpha,Zline+dalpha,Zline-1*dalpha,color='LightGray')
print dalpha
pl.scatter(zz - b*yy, xx,color='k')
pl.errorbar(zz-b*yy,xx,xerr=xerr,yerr=yerr,color='k',fmt='o')

pl.xlabel('log r$_e$ +'+'%.2f'%abs(b)+'log I$_e$')
pl.ylabel('log $\sigma$')
#pl.axis([0.8,1.35,0,0.6])
pl.show()

for key in dic.keys():
    lo,hi = np.percentile(dic[key][3000:].ravel(),16), np.percentile(dic[key][3000:].ravel(),84)
    med = dic[key][a1,a2]
    print key, '%.2f'%med, '$\pm$', '%.2f'%(np.mean((med-lo,hi-med)))
