"""FC70 rev 3: electrical fixes, JLC/LCSC parts, servo pin swap, full re-floorplan (built on cfg70)."""
import copy,cfg70
cfg=copy.deepcopy(cfg70.cfg)
cfg['rev']='3.0'; cfg['date']='2026-10-04'
cfg['comment1']='Rev 3: JLCPCBA release (EN UVLO, VREG caps, 3.3uH buck L, W25Q128, I2C 4.7k, servo pin swap, SD_CD)'
cfg['comment2']='Ø66 mm round board for 70 mm airframe, RP2350B'
cfg.setdefault('values',{})

_x,_y=[2400],[-80]
def _pos():
    p=(_x[0],_y[0]); _y[0]-=55
    if _y[0]<-1500: _y[0]=-80; _x[0]+=170
    return p
_new=[
 # 10 uF bulk at the microSD socket (card write current peaks)
 ('C35','C26','10uF','C15850','CL21A106KAYNNNE','C0805',{'1':'+3V3','2':'GND'}),
 # RP2350 IOVDD: one 100 nF per IOVDD pin group (rev 2 had too few for 8 IOVDD + QSPI/ADC/OTP pins)
 ('C36','C8','100nF','C1525','CL05B104KO5NNNC','C0402',{'1':'+3V3','2':'GND'}),
 ('C37','C8','100nF','C1525','CL05B104KO5NNNC','C0402',{'1':'+3V3','2':'GND'}),
 ('C38','C8','100nF','C1525','CL05B104KO5NNNC','C0402',{'1':'+3V3','2':'GND'}),
 ('C39','C8','100nF','C1525','CL05B104KO5NNNC','C0402',{'1':'+3V3','2':'GND'}),
 # high-frequency bypass at each TPS564201 VIN (TI DS 8.2.2.4: >=10 uF ceramic + small HF cap close to VIN/GND)
 ('C40','C8','100nF','C1525','CL05B104KO5NNNC','C0402',{'1':'BUCK5_VIN','2':'GND'}),
 ('C41','C8','100nF','C1525','CL05B104KO5NNNC','C0402',{'1':'BUCKSV_VIN','2':'GND'}),
 # 1 uF at AP2112K input (DS: 1 uF in/out), +5V rail arrives from the far side of the board
 ('C42','C8','1uF','C52923','CL05A105KA5NQNC','C0402',{'1':'+5V','2':'GND'}),
]
for ref,sym,val,lcsc,mpn,fp,pins in _new:
    cfg['extra'].append(dict(ref=ref,sym_from=sym,sch=_pos(),mpn=mpn,lcsc=lcsc))
    cfg['values'][ref]=val; cfg['fp_override'][ref]=fp
    for pn,net in pins.items(): cfg['pin_fixes'].append((f'{ref}.{pn}',net))

cfg['pin_fixes']+=[
 # RP2350 core regulator (Hardware design with RP2350, sec. 2.3): 4.7 uF on VREG_VIN, 4.7 uF on AVDD after 33R,
 # 4.7 uF on DVDD. Rev 2 had three 4.7 uF on AVDD and none on VREG_VIN.
 ('C4.1','+3V3'),('C5.1','+3V3'),
 # BNO055 BL_IND is an output (DS table 5-1): must not be tied to GND
 ('U2.10','NC'),
 # microSD: shell tabs to GND, card-detect to GPIO13 (internal pull-up)
 ('CARD1.12','GND'),('CARD1.13','GND'),('CARD1.9','SD_CD'),('U1.12','SD_CD'),
 # USB-C shell and JST-SH mounting tabs to GND
 ('USBC1.1','GND'),('USBC1.2','GND'),('USBC1.3','GND'),('USBC1.4','GND'),('CN2.0','GND'),
 # servo PWM moved to the left-hand GPIOs that face the servo connectors (GPIO38-41, unique PWM channels)
 ('U1.47','SERVO3_PWM'),('U1.48','SERVO2_PWM'),('U1.49','SERVO4_PWM'),('U1.52','SERVO1_PWM'),
 ('U1.79','NC'),('U1.80','NC'),('U1.1','NC'),('U1.2','NC'),
]

_B=dict
cfg['bom']={
 'C1':_B(value='15pF',lcsc='C1548',mpn='0402CG150J500NT'),'C2':_B(value='15pF',lcsc='C1548',mpn='0402CG150J500NT'),
 'C3':_B(value='4.7uF',lcsc='C19666',mpn='CL10A475KO8NNNC'),'C4':_B(value='4.7uF',lcsc='C19666',mpn='CL10A475KO8NNNC'),
 'C5':_B(value='4.7uF',lcsc='C19666',mpn='CL10A475KO8NNNC'),'C34':_B(value='4.7uF',lcsc='C19666',mpn='CL10A475KO8NNNC'),
 'C21':_B(value='22uF',lcsc='C45783',mpn='CL21A226MAQNNNE'),'C22':_B(value='22uF',lcsc='C45783',mpn='CL21A226MAQNNNE'),
 'C31':_B(value='22uF',lcsc='C45783',mpn='CL21A226MAQNNNE'),'C32':_B(value='22uF',lcsc='C45783',mpn='CL21A226MAQNNNE'),
 'C26':_B(value='10uF 25V',lcsc='C15850',mpn='CL21A106KAYNNNE'),'C29':_B(value='10uF 25V',lcsc='C15850',mpn='CL21A106KAYNNNE'),
 'C33':_B(value='10uF',lcsc='C15850',mpn='CL21A106KAYNNNE'),
 'CARD1':_B(value='TF-01A',lcsc='C91145',mpn='TF-01A'),'CN1':_B(value='XT30UPB-M',lcsc='C428721',mpn='XT30UPB-M'),
 'CN2':_B(value='BM04B-SRSS-TB',lcsc='C160390',mpn='BM04B-SRSS-TB(LF)(SN)'),
 'D1':_B(value='USBLC6-2SC6',lcsc='C7519',mpn='USBLC6-2SC6'),'D2':_B(value='SS14',lcsc='C112424',mpn='SS14'),
 'F1':_B(value='2.6A PTC',lcsc='C438899',mpn='SMD1812P260TF/16'),'F2':_B(value='3A PTC',lcsc='C20829',mpn='SMD2920P300TF/15'),
 'H1':_B(value='1x14 2.54',lcsc='C49569637',mpn='2011-1X14G00SB'),'H2':_B(value='SWD 1x3',lcsc='C49257',mpn='2.54-1*3P'),
 'L1':_B(value='3.3uH',lcsc='C42411119',mpn='AOTA-B201610S3R3-101-T'),
 'L2':_B(value='3.3uH',lcsc='C3002618',mpn='CKST0503-3.3uH/M'),'L3':_B(value='3.3uH',lcsc='C3002618',mpn='CKST0503-3.3uH/M'),
 'R1':_B(value='1k',lcsc='C11702',mpn='0402WGF1001TCE'),'R11':_B(value='1k',lcsc='C11702',mpn='0402WGF1001TCE'),
 'R2':_B(value='33',lcsc='C25105',mpn='0402WGF330JTCE'),
 'R5':_B(value='56k',lcsc='C25796',mpn='0402WGF5602TCE'),'R22':_B(value='56k',lcsc='C25796',mpn='0402WGF5602TCE'),
 'R6':_B(value='10k',lcsc='C25744',mpn='0402WGF1002TCE'),'R23':_B(value='10k',lcsc='C25744',mpn='0402WGF1002TCE'),
 'R7':_B(value='27',lcsc='C25100',mpn='0402WGF270JTCE'),'R8':_B(value='27',lcsc='C25100',mpn='0402WGF270JTCE'),
 'R10':_B(value='10mΩ 2W',lcsc='C192580',mpn='RLM25FEER010'),
 'R12':_B(value='5.1k',lcsc='C25905',mpn='0402WGF5101TCE'),'R13':_B(value='5.1k',lcsc='C25905',mpn='0402WGF5101TCE'),
 'R14':_B(value='100k',lcsc='C25803',mpn='0603WAF1003T5E'),'R24':_B(value='100k',lcsc='C25803',mpn='0603WAF1003T5E'),
 'R15':_B(value='33k',lcsc='C25779',mpn='0402WGF3302TCE'),'R17':_B(value='33k',lcsc='C25779',mpn='0402WGF3302TCE'),
 'R25':_B(value='4.7k',lcsc='C25900',mpn='0402WGF4701TCE'),'R26':_B(value='4.7k',lcsc='C25900',mpn='0402WGF4701TCE'),
 'SW2':_B(value='BOOTSEL',lcsc='C318884',mpn='TS-1187A-B-A-B'),
 'U1':_B(value='RP2350B',lcsc='C42415655',mpn='RP2350B'),'U2':_B(value='BNO055',lcsc='C93216',mpn='BNO055'),
 'U3':_B(value='BME680',lcsc='C125972',mpn='BME680'),'U4':_B(value='INA226',lcsc='C49851',mpn='INA226AIDGSR'),
 'U5':_B(value='LIS3MDL',lcsc='C478483',mpn='LIS3MDLTR'),
 'U6':_B(value='TPS564201',lcsc='C464812',mpn='TPS564201DDCR'),'U15':_B(value='TPS564201',lcsc='C464812',mpn='TPS564201DDCR'),
 'U7':_B(value='AP2112K-3.3',lcsc='C23380830',mpn='AP2112K-3.3TRG1'),
 'U8':_B(value='B3B-XH-A',lcsc='C144394',mpn='B3B-XH-A(LF)(SN)'),'U9':_B(value='B3B-XH-A',lcsc='C144394',mpn='B3B-XH-A(LF)(SN)'),
 'U10':_B(value='B3B-XH-A',lcsc='C144394',mpn='B3B-XH-A(LF)(SN)'),'U11':_B(value='B3B-XH-A',lcsc='C144394',mpn='B3B-XH-A(LF)(SN)'),
 'U12':_B(value='12MHz',lcsc='C20625731',mpn='ABM8-272-T3'),'U13':_B(value='SS-12D00-G3',lcsc='C22355741',mpn='SS-12D00-G3'),
 'U14':_B(value='W25Q128JVSIQ',lcsc='C97521',mpn='W25Q128JVSIQ'),
 'USBC1':_B(value='TYPE-C-31-M-12',lcsc='C165948',mpn='TYPE-C-31-M-12'),
}
for r in ['C6','C7','C8','C9','C10','C11','C12','C13','C14','C15','C16','C17','C18','C19','C20','C23','C24','C25','C27','C28','C30']:
    cfg['bom'][r]=_B(value='100nF',lcsc='C1525',mpn='CL05B104KO5NNNC')
for r in ['R9','R16','R18','R19','R20','R21']: cfg['bom'][r]=_B(value='10k',lcsc='C25744',mpn='0402WGF1002TCE')
cfg['dnp']=[]

# ---------------- rev 3 floorplan (all parts top side; absolute board coordinates, board centre 100,100, R 33.05)
P=cfg['pcb']
P['fixed']={}; P['autoplace']=[]; P['legacy']=None; P.pop('preroute',None); P['keepout']={}
P['floorplan']=dict(
 keep=['H1','H2','CN1','CARD1','CN2','U8','U9','U10','U11','U13','SW2','USBC1'],
 fixed={
  'U1':(100.12,98.41,180),
  # 5 V logic buck, top-left band under the header
  'L2':(90.6,80.6,0),'U15':(90.0,86.2,270),
  # servo buck next to the servo connectors
  'F2':(86.5,91.8,0),'U6':(85.6,97.2,270),'L3':(85.2,104.9,90),
  # battery entry: shunt, INA226, logic PTC (top right, beside XT30)
  'R10':(109.2,80.1,0),'F1':(109.6,84.6,0),'U4':(110.4,89.6,90),
  # 3V3 LDO and USB OR-ing diode
  'U7':(89.6,113.2,0),'D2':(106.6,121.4,90),
  # sensors on the side away from both inductors
  'U2':(109.8,100.6,0),'U5':(110.0,107.6,0),'U3':(110.6,114.2,0),
  # QSPI flash under the QSPI pins
  'U14':(98.6,111.0,0),
 },
 anchors={
  'U12':'U1.30','C1':'U12.1','R1':'U1.31','C2':'U12.3',
  'C26':'U15.3','C40':'U15.3','C6':'U15.6','R5':'U15.4','R6':'U15.4','R14':'U15.5','R15':'U15.5','C21':'L2.2','C22':'L2.2',
  'C29':'U6.3','C41':'U6.3','C30':'U6.6','R22':'U6.4','R23':'U6.4','R24':'U6.5','R17':'U6.5','C31':'L3.2','C32':'L3.2',
  'C33':'U7.5','C42':'U7.1',
  'L1':'U1.63','C34':'U1.65','R2':'U1.61','C3':'U1.61','C7':'U1.61','C4':'U1.64','C5':'U1.60',
  'C17':'U1.10','C19':'U1.32','C20':'U1.51',
  'C8':'U1.5','C9':'U1.15','C10':'U1.24','C11':'U1.29','C12':'U1.41','C13':'U1.50','C14':'U1.59','C15':'U1.68','C16':'U1.69','C18':'U1.76',
  'C36':'U14.8','C37':'U2.3','C38':'U2.28','C39':'U3.8','C23':'U5.5','C24':'U4.6','C25':'U5.4','C27':'U2.9','R9':'U2.11',
  'C28':'U1.35','R16':'U1.35','R11':'U14.1',
  'R7':'U1.67','R8':'U1.66','R12':'USBC1.A5','R13':'USBC1.B5','D1':'USBC1.A6',
  'R18':'CARD1.7','R19':'CARD1.8','R20':'CARD1.1','R21':'CARD1.2','C35':'CARD1.4',
  'R25':'CN2.3','R26':'CN2.4',
 },
 order_first=['U12','C1','R1','C2','L1','C34','R2','C3','C7','C4','C5','C17','C19','C20','R7','R8',
   'C26','C40','C6','R5','R6','R14','R15','C21','C22','C29','C41','C30','R22','R23','R24','R17','C31','C32'],
 margin=0.35,
 keepout={'U1':0.9,'MH1':0.6,'MH2':0.6,'MH3':0.6,'MH4':0.6},
)
P['in1_plane']=False
P['default_via']=(0.5,0.3)
P['netclasses']={'Power':(0.20,0.127,0.5,0.3),'HighCurrent':(0.20,0.15,0.8,0.4),'USB':(0.25,0.127,0.5,0.3,0.28,0.18)}
P['netclass_assign'].update({'VBAT':'HighCurrent','GND':'Power'})
P['fine_refs']=['U1','U2','U5']
P.update(default_track=(0.15,0.127),min_track=0.1,min_clear=0.1,gr_clr=0.11,gr_tw=0.1,gr_fine_zones=[(50,50,150,150)],gr_fine_clr=0.105)
P['widen']['Default']=[0.15,0.127]
P['extra_dru']="(rule \"Signal fine 3.9mil\" (condition \"A.NetClass == 'Default' && B.NetClass == 'Default'\") (constraint clearance (min 0.1mm)))\n"
# USB-C receptacle face 0.14 mm past the outline at its centre so a plug overmold never touches the board
P['floorplan']['keep'].remove('USBC1'); P['floorplan']['fixed']['USBC1']=(99.72,128.1,0)
# rev 3: keep the XH servo connector and the JST-SH clear of the M3 screw-head keepouts (MH3, MH4)
P['floorplan']['keep'].remove('U8'); P['floorplan']['fixed']['U8']=(80.0,115.21,90)
P['floorplan']['keep'].remove('CN2'); P['floorplan']['fixed']['CN2']=(118.0,114.01,180)
