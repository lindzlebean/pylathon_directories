import scipy,numpy,cPickle
import special_functions as sf
from scipy import ndimage,optimize,signal,interpolate
from numpy import linalg
from math import sqrt,log,log10
import pymc, myEmcee_blobs as myEmcee
import numpy as np, pylab as pl

light = 299792.458

def finddispersion(scispec,varspec,t1,t2,twave1,twave2,outwave,zl,zs,nfit=6,outfile=None,mask=None,bias=1e8,lim=4000.,bg='polynomial',restmask=None,srclim=6000.,lenslim=5500.,name=None):
    outwave,scispec,varspec = outwave[outwave>log10(lim)], scispec[outwave>log10(lim)], varspec[outwave>log10(lim)]

    if mask is not None:
        ma = np.ones(outwave.size)
        for M in mask:
            cond = np.where((outwave>np.log10(M[0]))&(outwave<np.log10(M[1])))
            ma[cond]=0
        if restmask is not None:
            for M in restmask:
                cond = np.where((outwave>np.log10(M[0]*(1.+zl)))&(outwave<np.log10(M[1]*(1.+zl))))
                ma[cond]=0
                cond = np.where((outwave>np.log10(M[0]*(1.+zs)))&(outwave<np.log10(M[1]*(1.+zs))))
                ma[cond]=0
        mask=ma==1
        outwave,scispec,varspec=outwave[mask],scispec[mask],varspec[mask]
    isig = 1./varspec**0.5
    ntemps1,ntemps2 = len(t1), len(t2)
    print 'BIAS!', bias
    
    if name is None:
        vL = pymc.Uniform('lens velocity',-1050.,1050.)#,value=2200.)
        sL = pymc.Uniform('lens dispersion',5.,501.)
        vS = pymc.Uniform('source velocity',-1050.,1050.)
        sS = pymc.Uniform('source dispersion',5.,501.)
    else:
        result = np.load('/data/ljo31b/EELs/esi/kinematics/inference/apertures/final/'+name+'_1.00_lens')
        lp,trace,dic,_=result
        a1,a2=np.unravel_index(lp.argmax(),lp.shape)
        vL = pymc.Uniform('lens velocity',-1050.,1050.,value=dic['lens velocity'][a1,a2])
        sL = pymc.Uniform('lens dispersion',5.,501.,value=dic['lens dispersion'][a1,a2])
        vS = pymc.Uniform('source velocity',-1050.,1050.,value=dic['source velocity'][a1,a2])
        sS = pymc.Uniform('source dispersion',5.,501.,value=dic['source dispersion'][a1,a2])
        print dic['lens velocity'][a1,a2], dic['lens dispersion'][a1,a2]
    pars = [vL,sL,vS,sS]
    cov = np.array([50.,10.,50.,10.])

    # Create the polynomial fit components
    BIAS = scispec*0.
    grid = 10**outwave[-1] - 10**outwave[0]
    operator = scipy.zeros((scispec.size,2*ntemps1+2*ntemps2+nfit))

    for i in range(nfit):
        p = scipy.zeros((nfit,1))
        p[i] = 1.
        coeff = {'coeff':p,'type':bg}
        poly = sf.genfunc(10**outwave,0.,coeff)
        operator[:,i+2*ntemps1+2*ntemps2] = poly
        BIAS += poly*bias/grid**i
        #pl.figure()
        #pl.plot(outwave, BIAS)
        #pl.show()

    oper = operator.T  
    cond = np.where(outwave<=np.log10(srclim),True,False)
    lenscond = np.where(outwave<np.log10(lenslim),True,False)
    @pymc.deterministic
    def logprob(value=0.,pars=pars):
        zL, zS = 1.+zl+vL.value/light, 1.+zs+vS.value/light
        owL1,owS1 = np.log10(twave1*zL), np.log10(twave1*zS)
        owL2,owS2 = np.log10(twave2*zL), np.log10(twave2*zS)
        osS, osL = sS.value*zS, sL.value*zL
        for k in range(ntemps1):
            a = interpolate.bisplev(osL,np.log10(twave1),t1[k])
            moda = interpolate.splrep(owL1,a)
            oper[k,~lenscond] = interpolate.splev(outwave[~lenscond],moda)
            b = interpolate.bisplev(osS,np.log10(twave1),t1[k])
            modb = interpolate.splrep(owS1,b)
            oper[k+ntemps1,~cond] = interpolate.splev(outwave[~cond],modb)  
        for k in range(ntemps2):
            a = interpolate.bisplev(osL,np.log10(twave2),t2[k])
            moda = interpolate.splrep(owL2,a)
            oper[k+2*ntemps1,lenscond] = interpolate.splev(outwave[lenscond],moda)
            b = interpolate.bisplev(osS,np.log10(twave2),t2[k])
            modb = interpolate.splrep(owS2,b)
            oper[k+2*ntemps1+ntemps2,cond] = interpolate.splev(outwave[cond],modb)  
        op = (oper*isig).T
        rhs = (scispec+BIAS)*isig
        fit,chi = optimize.nnls(op,rhs)
        lp = -0.5*chi**2.
        return lp
    
    @pymc.observed
    def logp(value=0.,lp=logprob):
        return lp
    print outfile
    S = myEmcee.Emcee(pars+[logp],cov=cov,nthreads=20,nwalkers=50)
    S.sample(400)
    outFile = '/data/ljo31b/EELs/esi/kinematics/inference/'+outfile
    f = open(outFile,'wb')
    cPickle.dump(S.result(),f,2)
    f.close()
    lp,trace,dic,_ = S.result()
    a1,a2 = numpy.unravel_index(lp.argmax(),lp.shape)
    for i in range(len(pars)):
        pars[i].value = trace[a1,a2,i]
        print "%18s  %8.3f"%(pars[i].__name__,pars[i].value)

    velL,sigL,velS,sigS = trace[a1,a2]
    
    zL, zS = 1.+zl+velL/light, 1.+zs+velS/light
    owL1,owS1 = np.log10(twave1*zL), np.log10(twave1*zS)
    owL2,owS2 = np.log10(twave2*zL), np.log10(twave2*zS)
    osS, osL = sigS*zS, sigL*zL

    for k in range(ntemps1):
        a = interpolate.bisplev(osL,np.log10(twave1),t1[k])
        moda = interpolate.splrep(owL1,a)
        oper[k,~lenscond] = interpolate.splev(outwave[~lenscond],moda)
        b = interpolate.bisplev(osS,np.log10(twave1),t1[k])
        modb = interpolate.splrep(owS1,b)
        oper[k+ntemps1,~cond] = interpolate.splev(outwave[~cond],modb)  
    for k in range(ntemps2):
        a = interpolate.bisplev(osL,np.log10(twave2),t2[k])
        moda = interpolate.splrep(owL2,a)
        oper[k+2*ntemps1,lenscond] = interpolate.splev(outwave[lenscond],moda)
        b = interpolate.bisplev(osS,np.log10(twave2),t2[k])
        modb = interpolate.splrep(owS2,b)
        oper[k+2*ntemps1+ntemps2,cond] = interpolate.splev(outwave[cond],modb)  
    op = (oper*isig).T
    rhs = (scispec+BIAS)*isig
    fit,chi = optimize.nnls(op,rhs)
    for i in range(nfit):
        fit[ntemps1*2+2*ntemps2+i] -= bias/grid**i
    outmodel = scipy.dot(oper.T,fit)
    continuum = scipy.dot(operator,fit)

    '''pl.figure()
    pl.plot(10**outwave,scispec)
    pl.plot(10**outwave,outmodel)
    pl.plot(10**outwave,continuum)
    pl.figure()
    pl.plot(lp)
    pl.show()'''
    return S.result()

def readresults(scispec,varspec,t1,t2,twave1,twave2,outwave,zl,zs,nfit=6,infile=None,mask=None,bias=1e8,lim=5000.,bg='polynomial',restmask=None,srclim=6000.,lenslim=5500.):
    outwave,scispec,varspec = outwave[outwave>log10(lim)], scispec[outwave>log10(lim)], varspec[outwave>log10(lim)]
    origwave,origsci,origvar = outwave.copy(),scispec.copy(),varspec.copy()
    if mask is not None:
        ma = np.ones(outwave.size)
        for M in mask:
            cond = np.where((outwave>np.log10(M[0]))&(outwave<np.log10(M[1])))
            ma[cond]=0
        if restmask is not None:
            for M in restmask:
                cond = np.where((outwave>np.log10(M[0]*(1.+zl)))&(outwave<np.log10(M[1]*(1.+zs))))
                ma[cond]=0
                cond = np.where((outwave>np.log10(M[0]*(1.+zs)))&(outwave<np.log10(M[1]*(1.+zs))))
                ma[cond]=0
        ma=ma==1
        outwave,scispec,varspec=outwave[ma],scispec[ma],varspec[ma]
    isig = 1./varspec**0.5
    ntemps1,ntemps2 = len(t1), len(t2)
 
   # Create the polynomial fit components
    BIAS = scispec*0.
    grid = 10**outwave[-1] - 10**outwave[0]
    operator = scipy.zeros((scispec.size,2*ntemps1+2*ntemps2+nfit))
    for i in range(nfit):
        p = scipy.zeros((nfit,1))
        p[i] = 1.
        coeff = {'coeff':p,'type':bg}
        poly = sf.genfunc(10**outwave,0.,coeff)
        operator[:,i+2*ntemps1+2*ntemps2] = poly
        BIAS += bias*poly/grid**i

    oper = operator.T 
    cond = np.where(outwave<=np.log10(srclim),True,False)
    lenscond = np.where(outwave<np.log10(lenslim),True,False)

    result = np.load('/data/ljo31b/EELs/esi/kinematics/inference/'+infile)
    lp,trace,dic,_=result
    a1,a2 = numpy.unravel_index(lp.argmax(),lp.shape)
    velL,sigL,velS,sigS = trace[a1,a2]

    zL, zS = 1.+zl+velL/light, 1.+zs+velS/light
    owL1,owS1 = np.log10(twave1*zL), np.log10(twave1*zS)
    owL2,owS2 = np.log10(twave2*zL), np.log10(twave2*zS)
    osS, osL = sigS*zS, sigL*zL

    for k in range(ntemps1):
        a = interpolate.bisplev(osL,np.log10(twave1),t1[k])
        moda = interpolate.splrep(owL1,a)
        oper[k,~lenscond] = interpolate.splev(outwave[~lenscond],moda)
        b = interpolate.bisplev(osS,np.log10(twave1),t1[k])
        modb = interpolate.splrep(owS1,b)
        oper[k+ntemps1,~cond] = interpolate.splev(outwave[~cond],modb)  
    for k in range(ntemps2):
        a = interpolate.bisplev(osL,np.log10(twave2),t2[k])
        moda = interpolate.splrep(owL2,a)
        oper[k+2*ntemps1,lenscond] = interpolate.splev(outwave[lenscond],moda)
        b = interpolate.bisplev(osS,np.log10(twave2),t2[k])
        modb = interpolate.splrep(owS2,b)
        oper[k+2*ntemps1+ntemps2,cond] = interpolate.splev(outwave[cond],modb)      
        
    op = (oper*isig).T
    rhs = (scispec+BIAS)*isig
    fit,chi = optimize.nnls(op,rhs)
    for i in range(nfit):
        fit[ntemps1*2+ntemps2*2+i] -= bias/grid**i
    maskmodel = scipy.dot(oper.T,fit)
    # unmasked
    if mask is not None or restmask is not None:
        operator = scipy.zeros((origsci.size,2*ntemps1+2*ntemps2+nfit))
        
        for i in range(nfit):
            p = scipy.zeros((nfit,1))
            p[i] = 1.
            coeff = {'coeff':p,'type':bg}
            poly = sf.genfunc(10**origwave,0.,coeff)
            operator[:,i+2*ntemps1+2*ntemps2] = poly

        oper = operator.T 
        origcond = np.where(origwave<=np.log10(srclim),True,False)
        origlenscond = np.where(origwave<np.log10(lenslim),True,False)

        for k in range(ntemps1):
            a = interpolate.bisplev(osL,np.log10(twave1),t1[k])
            moda = interpolate.splrep(owL1,a)
            oper[k,~origlenscond] = interpolate.splev(origwave[~origlenscond],moda)
            b = interpolate.bisplev(osS,np.log10(twave1),t1[k])
            modb = interpolate.splrep(owS1,b)
            oper[k+ntemps1,~origcond] = interpolate.splev(origwave[~origcond],modb)  
        for k in range(ntemps2):
            a = interpolate.bisplev(osL,np.log10(twave2),t2[k])
            moda = interpolate.splrep(owL2,a)
            oper[k+2*ntemps1,lenscond] = interpolate.splev(outwave[lenscond],moda)
            b = interpolate.bisplev(osS,np.log10(twave2),t2[k])
            modb = interpolate.splrep(owS2,b)
            oper[k+2*ntemps1+ntemps2,origcond] = interpolate.splev(origwave[origcond],modb)      
        
    outmodel = scipy.dot(oper.T,fit)
    lens = scipy.dot(oper[:ntemps1].T,fit[:ntemps1]) + scipy.dot(oper[ntemps1*2:ntemps1*2+ntemps2].T,fit[ntemps1*2:ntemps1*2+ntemps2])
    source = scipy.dot(oper[2*ntemps1+ntemps2:2*ntemps1+2*ntemps2].T,fit[2*ntemps1+ntemps1:2*ntemps1+2*ntemps2]) + scipy.dot(oper[ntemps1:2*ntemps1].T,fit[ntemps1:2*ntemps1])
    cont = scipy.dot(oper[2*ntemps1+2*ntemps2:].T,fit[2*ntemps1+2*ntemps2:])
    
    #print restmask
    pl.figure()
    if mask is not None:
        for M in mask:
            pl.axvspan(M[0], M[1], color='DarkGray')
    if restmask is not None:
        for M in restmask:
            pl.axvspan(M[0]*(1.+zl),M[1]*(1.+zl),color='DarkGray')
            pl.axvspan(M[0]*(1.+zs), M[1]*(1.+zs),color='DarkGray')
    pl.plot(10**origwave,origsci,'LightGray')
    pl.plot(10**origwave,outmodel,'k')
    pl.plot(10**origwave,lens,'SteelBlue',label='lens')
    pl.plot(10**origwave,source,'Crimson',label='source')
    pl.plot(10**origwave,cont,'Navy')
    pl.legend(loc='upper right',frameon=False)
    pl.xlabel('observed wavelength ($\AA$)')
    pl.ylabel('flux (arbitrary units)')
    pl.axis([lim,9500,-0.5,4])
    pl.figtext(0.15,0.8,r'$\sigma_{s,old} = $'+'%.2f'%sigS+'; $\sigma_{l,old} = $'+'%.2f'%sigL)

    #pl.show()
    #pl.figure()
    #pl.plot(10**outwave,scispec-maskmodel,'k')
    print '%.2f'%velL, '%.2f'%sigL,'%.2f'%velS,'%.2f'%sigS
    for i in fit:
        print i
    return result

