import numpy as np, pyfits as py

tablelens = py.open('/data/ljo31/Lens/LensParams/Phot_2src_lensgals_new.fits')[1].data
table = py.open('/data/ljo31/Lens/LensParams/Phot_2src_new.fits')[1].data
tablek = py.open('/data/ljo31/Lens/LensParams/KeckPhot_2src_new.fits')[1].data
tableklens = py.open('/data/ljo31/Lens/LensParams/KeckGalPhot_2src_new.fits')[1].data
names = table['name']
# need to add J1619 into K band tables. I did say I would do this today.

dic = []
for i in range(len(names)):
    dic.append((names[i],[table['mag v'][i],table['mag i'][i],np.min((table['mag v hi'][i],table['mag v lo'][i])),np.min((table['mag i hi'][i],table['mag i lo'][i])),table['v-i'][i],np.min((table['v-i lo'][i], table['v-i hi'][i])),tablelens['mag v'][i],tablelens['mag i'][i],np.min((tablelens['mag v hi'][i],tablelens['mag v lo'][i])),np.min((tablelens['mag i hi'][i],tablelens['mag i lo'][i])),tablelens['v-i'][i],np.min((tablelens['v-i lo'][i], tablelens['v-i hi'][i])),tablek['mag k'][i],np.min((tablek['mag k lo'][i],tablek['mag k hi'][i])),tableklens['mag k'][i],np.min((tableklens['mag k lo'][i],tableklens['mag k hi'][i]))]))

dic = dict(dic)
np.save('/data/ljo31/Lens/LensParams/VIK_phot_212_dict',dic)

'''
sdssdata = np.loadtxt('/data/ljo31/Lens/LensParams/SDSS_phot_dereddened.txt')
dic = []
for i in range(len(names)):
    dic.append((names[i],sdssdata[i].tolist()))

dic = dict(dic)
np.save('/data/ljo31/Lens/LensParams/SDSS_phot_dereddened_dict',dic)
'''

sdssdata = np.loadtxt('/data/ljo31/Lens/LensParams/SDSS_phot_dereddened.txt')
dic = []
for i in range(len(names)):
    dic.append((names[i],sdssdata[i].tolist()))

dic = dict(dic)
np.save('/data/ljo31/Lens/LensParams/SDSS_phot_dereddened_dict',dic)


tablelens = py.open('/data/ljo31/Lens/LensParams/Phot_1src_lensgals_new.fits')[1].data
table = py.open('/data/ljo31/Lens/LensParams/Phot_1src_new.fits')[1].data
tablek = py.open('/data/ljo31/Lens/LensParams/KeckPhot_1src_new.fits')[1].data
tableklens = py.open('/data/ljo31/Lens/LensParams/KeckGalPhot_1src_new.fits')[1].data
names = table['name']


dic = []
for i in range(len(names)):
    print names[i]
    dic.append((names[i],[table['mag v'][i],table['mag i'][i],np.min((table['mag v hi'][i],table['mag v lo'][i])),np.min((table['mag i hi'][i],table['mag i lo'][i])),table['v-i'][i],np.min((table['v-i lo'][i], table['v-i hi'][i])),tablelens['mag v'][i],tablelens['mag i'][i],np.min((tablelens['mag v hi'][i],tablelens['mag v lo'][i])),np.min((tablelens['mag i hi'][i],tablelens['mag i lo'][i])),tablelens['v-i'][i],np.min((tablelens['v-i lo'][i], tablelens['v-i hi'][i])),tablek['mag k'][i],np.min((tablek['mag k lo'][i],tablek['mag k hi'][i])),tableklens['mag k'][i],np.min((tableklens['mag k lo'][i],tableklens['mag k hi'][i]))]))

dic = dict(dic)
np.save('/data/ljo31/Lens/LensParams/VIK_phot_211_dict',dic)
