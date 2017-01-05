import numpy as np, pylab as pl, pyfits as py, cPickle
from linslens.ClipResult import clipburnin
from astLib import astCalc

names = py.open('/data/ljo31/Lens/LensParams/Phot_1src_huge_new.fits')[1].data['name']
'''masses = np.zeros((6,len(names)))
ii = 0
for name in names:                  
    lo,med,hi=np.load('/data/ljo31b/EELs/inference/new/211_params_'+name+'.npy').T
    masses[:,ii] = np.array([med[-1],med[-1]-lo[-1],hi[-1]-med[-1], med[2], med[2]-lo[2],hi[2]-med[2]])
    print masses[:,ii]
    ii+=1
    
filename = '/data/ljo31b/EELs/inference/new/masses.npy'
f = open(filename, "wb")
np.save(f,masses)
f.close()
''' 
masses = np.zeros((6,len(names)))
ii = 0
for name in names: 
    lo,med,hi=np.load('/data/ljo31b/EELs/inference/new/huge/212_params_'+name+'.npy').T
    
    masses[:,ii] = np.array([med[-1],med[-1]-lo[-1],hi[-1]-med[-1], med[2], med[2]-lo[2],hi[2]-med[2]])
    print masses[:,ii]
    ii+=1
    
filename = '/data/ljo31b/EELs/inference/new/huge/masses_212.npy'
f = open(filename, "wb")
np.save(f,masses)
f.close()

massnew = np.load('/data/ljo31b/EELs/inference/new/huge/masses_212.npy')
src_new = massnew[3]
lens_new = massnew[0]
massold = np.load('/data/ljo31b/EELs/inference/new/masses_212.npy')
src_old = massold[3]
lens_old = massold[0]

'''
sdssdata = np.load('/data/ljo31/Lens/LensParams/SDSS_phot_dereddened_dict_new.npy')[()]
vkidata = np.load('/data/ljo31/Lens/LensParams/VIK_phot_211_dict_new.npy')[()]
Ahst = np.load('/data/ljo31/Lens/LensParams/Alambda_hst.npy')[()]
Akeck = np.load('/data/ljo31/Lens/LensParams/Alambda_keck.npy')[()]
bands = np.load('/data/ljo31/Lens/LensParams/HSTBands.npy')[()]

array = np.zeros((
for name in names:
    g,r,i,z,dg,dr,di,dz = sdssdata[name]
    v_src,i_src,dv_src,di_src,vi_src,dvi_src, v_lens,i_lens,dv_lens,di_lens,vi_lens,dvi_lens, k_src, dk_src, k_lens, dk_lens = vkidata[name]
    v_src, v_lens = v_src - Ahst[name][0], v_lens - Ahst[name][0]
    i_src, i_lens = i_src - Ahst[name][1], i_lens - Ahst[name][1]
    k_src,k_lens = k_src - Akeck[name], k_lens - Akeck[name]
    array[:,ii] = np.array([med[-1],med[-1]-lo[-1],hi[-1]-med[-1], med[2], med[2]-lo[2],hi[2]-med[2],g,r,i,z,dg,dr,di,dz,v_src,i_src,dv_src,di_src,vi_src,dvi_src, v_lens,i_lens,dv_lens,di_lens,vi_lens,dvi_lens, k_src, dk_src, k_lens, dk_lens])

'''
