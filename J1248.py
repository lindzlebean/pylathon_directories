import pyfits as py, numpy as np, pylab as pl

name = 'J1248+4711'


# load V-band science data, cut out the lens system and plot it
V = py.open('/data/ljo31/Lens/'+str(name[:5])+'/SDSS'+str(name)+'_F555W_sci.fits')[0].data.copy()
header = py.open('/data/ljo31/Lens/'+str(name[:5])+'/SDSS'+str(name)+'_F555W_sci.fits')[0].header.copy()

Vcut=V[2435:2580,3470:3620]
print Vcut.shape

#Vcut[Vcut<-1] = 0
pl.figure()
pl.imshow(np.log10(Vcut),origin='lower',interpolation='nearest')

# load V-band weight data, cut it and plot it
V_wht = py.open('/data/ljo31/Lens/'+str(name[:5])+'/SDSS'+str(name)+'_F555W_wht.fits')[0].data.copy()
header_wht = py.open('/data/ljo31/Lens/'+str(name[:5])+'/SDSS'+str(name)+'_F555W_wht.fits')[0].header.copy()
V_wht_cut = V_wht[2435:2580,3470:3620]

#Vcut[Vcut<-1] = 0
pl.figure()
pl.imshow(np.log10(V_wht_cut),origin='lower',interpolation='nearest')

# save both
#py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F555W_sci_cutout.fits',Vcut,header,clobber=True)
#py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F555W_wht_cutout.fits',V_wht_cut,header_wht,clobber=True)

'''psfs'''
psf1=V[2718-14:2718+14,3361-14:3361+14]
psf1=psf1[:-2,:-1]
psf2 = V[1864-14:1864+14,4353-14:4353+14]
psf2=psf2[:-1,:-1]


psf1 = psf1/np.sum(psf1)
psf2 = psf2/np.sum(psf2)

pl.figure()
pl.imshow((psf1),interpolation='nearest',cmap='hot_r')
pl.figure()
pl.imshow((psf2),interpolation='nearest')

#py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F555W_psf1.fits', psf1, clobber=True)
#py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F555W_psf2.fits', psf2, clobber=True)


''' I BAND '''
# load V-band science data, cut out the lens system and plot it
I = py.open('/data/ljo31/Lens/'+str(name[:5])+'/SDSS'+str(name)+'_F814W_sci.fits')[0].data.copy()
header = py.open('/data/ljo31/Lens/'+str(name[:5])+'/SDSS'+str(name)+'_F814W_sci.fits')[0].header.copy()
Icut = I[2435:2580,3470:3620]

pl.figure()
pl.imshow(np.log10(Icut),origin='lower',interpolation='nearest')

# load I-band weight data, cut it and plot it
I_wht = py.open('/data/ljo31/Lens/'+str(name[:5])+'/SDSS'+str(name)+'_F814W_wht.fits')[0].data.copy()
header_wht = py.open('/data/ljo31/Lens/'+str(name[:5])+'/SDSS'+str(name)+'_F814W_wht.fits')[0].header.copy()
I_wht_cut = I_wht[2435:2580,3470:3620]

pl.figure()
pl.imshow(np.log10(I_wht_cut),origin='lower',interpolation='nearest')

# save both
#py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F814W_sci_cutout.fits',Icut,header,clobber=True)
#py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F814W_wht_cutout.fits',I_wht_cut,header_wht,clobber=True)



'''psfs! how dull they are '''
'''psf1=I[2718-14:2718+14,3361-14:3361+14]
psf1 = psf1[:-2,:-1]

psf2 = I[4085-14:4085+14,130-14:130+14]
psf2 = psf2[:-2,:-1]

psf3 = I[3900-14:3900+14,3995-14:3995+14]
psf3 = psf3[:-1,:-2]

psf1 = psf1/np.sum(psf1)
psf2 = psf2/np.sum(psf2)
psf3=psf3/np.sum(psf3)

pl.figure()
pl.imshow((psf1),interpolation='nearest')
pl.figure()
pl.imshow((psf2),interpolation='nearest')
pl.figure()
pl.imshow((psf3),interpolation='nearest')


py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F814W_psf1.fits', psf1, clobber=True)
py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F814W_psf2.fits', psf2, clobber=True)
py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F814W_psf3.fits', psf3, clobber=True)'''

psf1=I[2718-24:2718+24,3361-24:3361+24]
psf1 = psf1[:-2,:-1]

psf2 = I[4085-24:4085+24,130-24:130+24]
psf2 = psf2[:-2,:-1]

psf3 = I[3900-24:3900+24,3995-24:3995+24]
psf3 = psf3[:-1,:-2]

psf1 = psf1/np.sum(psf1)
psf2 = psf2/np.sum(psf2)
psf3=psf3/np.sum(psf3)

pl.figure()
pl.imshow((psf1),interpolation='nearest')
pl.figure()
pl.imshow((psf2),interpolation='nearest')
pl.figure()
pl.imshow((psf3),interpolation='nearest')


py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F814W_psf1_big.fits', psf1, clobber=True)
py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F814W_psf2_big.fits', psf2, clobber=True)
py.writeto('/data/ljo31/Lens/'+str(name[:5])+'/F814W_psf3_big.fits', psf3, clobber=True)


psf1 = I[4085-15:4085+15,130-15:130+15]
