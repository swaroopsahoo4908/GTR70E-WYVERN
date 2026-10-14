TITLE='GTR70E WYVERN Flight Computer (70 mm airframe)'
cfg=dict(
 name='WYVERN-E_FC70', title='GTR70E WYVERN FC-70 Flight Computer', date='2026-10-02', rev='2.0',
 company='WYVERN-E program', comment1='Converted from EasyEDA Pro WYVERN-E 1.0 (2026-08-13, netlist rev 21)',
 comment2='Ø66 mm round board for 70 mm airframe, RP2350B',
 epru='/tmp/w/e70/WYVERN-E 1.0.epru', tel='/tmp/w/nl/Netlist_Schematic1_2026-08-13_(21).tel',
 removed=['R3','R4'],
 extra=[
  dict(ref='U6',sym_from='U15',sch=(2060,-920),mpn='TPS564201DDCR',lcsc='C2069847'),
  dict(ref='L3',sym_from='L2',sch=(2025,-830),mpn='CKST0503-2.2UH/M'),
  dict(ref='F2',sym_from='F1',sch=(1960,-990),mpn='PTC 2920 (servo rail, size per servo stall current)'),
  dict(ref='C29',sym_from='C26',sch=(1940,-800),mpn='CL21B106KOQNNNE'),
  dict(ref='C30',sym_from='C6',sch=(2145,-930),mpn='CC0402KRX7R9BB104'),
  dict(ref='C31',sym_from='C21',sch=(2065,-765),mpn='CL21A226MPQNNNE'),
  dict(ref='C32',sym_from='C22',sch=(2065,-715),mpn='CL21A226MPQNNNE'),
  dict(ref='R22',sym_from='R5',sch=(2105,-830),mpn='RC0402FR-0756KL'),
  dict(ref='R23',sym_from='R6',sch=(2155,-830),mpn='0402WGF1022TCE'),
  dict(ref='R24',sym_from='R14',sch=(1960,-1045),mpn='0603WAF1003T5E'),
  dict(ref='C33',sym_from='C26',sch=(760,-1555),mpn='CL21B106KOQNNNE'),
  dict(ref='C34',sym_from='C3',sch=(620,-1545),mpn='CL10A475KA8NQNC'),
  dict(ref='R25',sym_from='R9',sch=(1520,-480),mpn='FRC0402F1002TS'),
  dict(ref='R26',sym_from='R9',sch=(1520,-450),mpn='FRC0402F1002TS'),
 ],
 fp_override={'U13':'SW-TH_3P-L8.8-W3.9-P2.50_SS12D00G3','F2':'Fuse_2920_7451Metric','R17':'R0603','R24':'R0603'},
 pin_fixes=[('U12.2','GND'),('U12.3','XOUT_R')],   # crystal: pins 1/3 are the resonator, 2/4 case GND
 netnames={'$1N586':'GND','$1N536':'+3V3','$1N589':'+1V1_DVDD','$1N509':'VSERVO','$1N541':'+5V','$1N357':'I2C_SDA','$1N359':'I2C_SCL',
  '$1N380':'VREG_AVDD','$1N387':'USBC_DP','$1N388':'USBC_DN','$1N587':'VBAT_SHUNT','$1N373':'VBUS','$1N588':'VBAT','$1N368':'BUCK5_FB',
  '$1N370':'BUCK5_SW','$1N398':'SWDIO','$1N399':'SWCLK','$1N409':'SD_CS','$1N425':'XIN','$1N438':'QSPI_SS','$1N439':'BOOTSEL_R',
  '$1N460':'SD_DAT0_MISO','$1N500':'RUN','$1N513':'BUCKSV_VIN','$1N514':'BUCKSV_SW','$1N518':'BUCKSV_FB','$1N543':'BUCK5_EN',
  '$1N564':'PWR_EN','$1N566':'XOUT_R','$1N568':'BUCKSV_EN','$1N582':'BUCK5_VIN','$1N371':'BUCK5_BST','$1N378':'VREG_LX','$1N391':'USB_DP',
  '$1N392':'SERVO1_PWM','$1N393':'SERVO2_PWM','$1N394':'SERVO3_PWM','$1N395':'SERVO4_PWM','$1N400':'HDR_GPIO37','$1N401':'HDR_GPIO36',
  '$1N402':'HDR_GPIO35','$1N403':'HDR_GPIO34','$1N404':'HDR_GPIO12','$1N413':'USB_DN','$1N449':'QSPI_SD1','$1N450':'QSPI_SD2',
  '$1N451':'QSPI_SD0','$1N452':'QSPI_SCLK','$1N453':'QSPI_SD3','$1N456':'MAG_C1','$1N473':'USB_CC1','$1N479':'USB_CC2','$1N494':'IMU_NRST',
  '$1N495':'IMU_CAP','$1N507':'SD_DAT1','$1N515':'BUCKSV_BST','$1N527':'SD_CMD_MOSI','$1N529':'SD_DAT2','$1N530':'SD_CLK','$1N565':'XOUT'},
)
cfg['pcb']=dict(layers=4,
 netclasses={ # name: (track, clearance, via, drill, [dp width, dp gap])
   'Power':(0.20,0.127,0.6,0.3),
   'HighCurrent':(0.20,0.15,0.8,0.4),
   'USB':(0.25,0.127,0.6,0.3,0.28,0.18),
 },
 netclass_assign={'+3V3':'Power','+1V1_DVDD':'Power','VREG_AVDD':'Power','VREG_LX':'Power','BUCK5_BST':'Power','BUCKSV_BST':'Power',
   'VBAT':'HighCurrent','VBAT_SHUNT':'HighCurrent','BUCK5_VIN':'HighCurrent','BUCKSV_VIN':'HighCurrent','+5V':'HighCurrent','VSERVO':'HighCurrent',
   'BUCK5_SW':'HighCurrent','BUCKSV_SW':'HighCurrent','VBUS':'HighCurrent','GND':'Power',
   'USB_DP':'USB','USB_DN':'USB','USB_DM':'USB','USBC_DP':'USB','USBC_DN':'USB'},
)
# (ref, anchor ref or (x,y) abs, sides)
cfg['pcb']['autoplace']=[
 ('U6',(84,100),('B',)),('L3','U6',('B',)),('C30','U6',('B',)),('C29','U6',('B',)),('F2','C29',('B',)),
 ('C31','L3',('B',)),('C32','L3',('B',)),('R22','U6',('B',)),('R23','U6',('B',)),('R24','U6',('B',)),('R17','U6',('B',)),
 ('C27','U2',('F','B')),('C28','U1',('F','B')),('R16','U1',('F','B')),('C34','L1',('F','B')),('C33','U7',('F','B')),
 ('R18','CARD1',('F','B')),('R19','CARD1',('F','B')),('R20','CARD1',('F','B')),('R21','CARD1',('F','B')),
 ('R25','CN2',('F','B')),('R26','CN2',('F','B')),('R14','U15',('F','B')),('R15','U15',('F','B')),
]

cfg['pcb']['widen']={'HighCurrent':[1.5,1.2,1.0,0.8,0.6,0.5,0.4,0.3],'Power':[0.5,0.4,0.3,0.25],'USB':[0.28]}

cfg['pcb']['rip_groups']=[['QSPI_SCLK','QSPI_SD0','QSPI_SD1','QSPI_SD2','QSPI_SD3','QSPI_SS']]

cfg['pcb']['keepout']={'U1':2.5,'U2':0.6,'U5':0.6,'U4':0.6}

cfg['pcb']['legacy']={'layers':[1,2]}

_o=(90.0,103.0)
def _a(dx,dy,ang=0): return dict(x=_o[0]+dx,y=_o[1]+dy,angle=ang,side='B',abs=True)
cfg['pcb']['fixed']={'U6':_a(0,0),'C30':_a(2.3,0,90),'L3':_a(0,5.2),'C31':_a(-3.8,9.4),'C32':_a(1.1,9.4),
  'C29':_a(-3.2,0,90),'F2':_a(-7.6,1.0,90),'R22':_a(-1.5,-3.0),'R23':_a(-1.5,-4.2),'R24':_a(1.9,-3.0),'R17':_a(1.9,-4.5)}
cfg['pcb']['autoplace']=[a for a in cfg['pcb']['autoplace'] if a[0] not in cfg['pcb']['fixed']]
cfg['pcb']['ap_margin']=0.5

cfg['pcb']['fixed']['U14']=dict(x=101.0,y=111.2,angle=90,side='B',abs=True)
cfg['pcb']['preroute']=['QSPI_SD2','QSPI_SD0','QSPI_SD1','QSPI_SCLK','QSPI_SS','QSPI_SD3']
