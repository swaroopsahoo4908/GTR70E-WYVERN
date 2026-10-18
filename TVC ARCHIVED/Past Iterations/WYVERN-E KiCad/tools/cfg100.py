LDO=dict(pins=[dict(x=-30,y=0,len=10,rot=0,num='3',name='VIN',type='Undefined',shape='NONE'),
               dict(x=30,y=0,len=10,rot=180,num='2',name='VOUT',type='Undefined',shape='NONE'),
               dict(x=0,y=-20,len=10,rot=90,num='1',name='GND/ADJ',type='Undefined',shape='NONE')],
         gfx=[('RECT',dict(dotX1=-20,dotY1=10,dotX2=20,dotY2=-10))],bbox=[-20,-10,20,10])
TP=dict(pins=[dict(x=0,y=-10,len=5,rot=90,num='1',name='1',type='Undefined',shape='NONE')],
        gfx=[('CIRCLE',dict(centerX=0,centerY=0,radius=4))],bbox=[-4,-4,4,4])
cfg=dict(
 name='WYVERN-E_FC100', title='WYVERN-E FC-100 Flight Computer (100 mm airframe)', date='2026-10-02', rev='2.0',
 company='WYVERN-E program', comment1='Converted from EasyEDA Pro WYVERN-E (2026-08-09), 4-layer',
 comment2='92 mm round board, RP2350B + ADAU1450 + BQ25798',
 epru='/tmp/w/x_new/WYVERN-E.epru',
 removed=[],
 extra=[
  dict(ref='U34',part=LDO,part_name='AMS1117-1.2',sch=(2050,-1300),mpn='AMS1117-1.2',lcsc=''),
  dict(ref='C35',sym_from='C7',sch=(2130,-1330),mpn='CL21A226MAQNNNE (22uF 0805)'),
  dict(ref='C36',sym_from='C7',sch=(1985,-1330),mpn='CL21A106KAYNNNE (10uF 0805)'),
  dict(ref='TP1',part=TP,part_name='TestPoint',sch=(300,-1000),mpn='Test pad SWCLK'),
 ],
 values={'C35':'22uF','C36':'10uF','U34':'AMS1117-1.2','TP1':'SWCLK'},
 fp_override={'U34':'SOT-223-3_TabPin2','TP1':'TestPoint_Pad_D1.5mm','C35':'C0805','C36':'C0805'},
 netnames_by_pin={'U1.81':'GND','U1.15':'+3V3','U1.10':'+1V1_DVDD','R7.1':'VSERVO','R12.1':'VBAT','R3.2':'VBAT_RAW','C10.1':'VSYS',
   'U3.2':'VBUS','L3.2':'VSERVO_PRE','U1.14':'I2C1_SCL','U1.13':'I2C1_SDA','U1.12':'I2C0_SCL_SENS','U1.11':'I2C0_SDA_SENS',
   'U1.66':'USB_DN','U1.67':'USB_DP','U1.16':'SD_MISO','U1.17':'SD_CS','U1.18':'SD_SCK','U1.19':'SD_MOSI','U1.20':'SD_CD',
   'R4.2':'BUCK_SV_FB_MID','U18.21':'DSP_XTALIN','U18.22':'DSP_XTALOUT','U1.30':'XIN','U1.31':'XOUT','U3.5':'BQ_REGN',
   'U3.26':'BQ_SW2','U3.28':'BQ_SW1','U4.2':'BUCK3V3_SW','U5.2':'BUCKSV_SW','U4.4':'BUCK3V3_FB','U5.4':'BUCKSV_FB',
   'U21.2':'PYRO1_OUT','U33.2':'PYRO2_OUT','Q1.1':'PYRO1_GATE','Q2.1':'PYRO2_GATE','U1.35':'RUN','U1.63':'VREG_LX','U17.2':'PDM_CLK','U17.3':'PDM_DATA','U18.58':'DSP_LRCLK','U1.71':'QSPI_SCLK','U1.75':'QSPI_SS_FLASH','U1.72':'QSPI_SD0','U1.74':'QSPI_SD1','U1.73':'QSPI_SD2','U1.70':'QSPI_SD3','U1.42':'PSRAM_CS','U12.10':'PYRO1_DRV','U12.11':'PYRO2_DRV','U12.12':'PYRO1_CONT','U12.13':'PYRO2_CONT','U18.24':'DSP_RESET','U18.16':'DSP_PLLFILT','U1.40':'LED1_DRV'},
 pin_fixes=[
  ('U1.33','SWCLK'),('TP1.1','SWCLK'),
  ('U11.6','+3V3'),('U11.8','+3V3'),('U11.7','GND'),('U11.3','@U13.11'),('U11.5','GND'),
  ('U1.59','+3V3'),('U1.68','+3V3'),('C1.1','+3V3'),
  ('U18.20','+1V2_DSP'),('U18.35','+1V2_DSP'),('U18.53','+1V2_DSP'),('U18.71','+1V2_DSP'),('U18.3','GND'),('U18.72','GND'),
  ('U34.1','GND'),('U34.2','+1V2_DSP'),('U34.3','+3V3'),('C35.1','+1V2_DSP'),('C35.2','GND'),('C36.1','+3V3'),('C36.2','GND'),
  ('X2.1','@U18.21'),('X2.3','@U18.22'),('X2.2','GND'),('X2.4','GND'),
  ('USBC1.B6','@USBC1.A6'),('USBC1.B7','@USBC1.A7'),('USBC1.B4A9','@USBC1.A4B9'),
  ('USBC1.1','GND'),('USBC1.2','GND'),('USBC1.3','GND'),('USBC1.4','GND'),
  ('U14.6','+3V3'),('U15.5','GND'),('U15.6','GND'),
  ('CN1.1','GND'),('CN1.2','@R3.2'),
  ('U3.20','BQ_PROG'),('R12.1','BQ_PROG'),
  ('CARD1.4','+3V3'),('CARD1.6','GND'),('CARD1.7','@U1.16'),('CARD1.5','@U1.18'),('CARD1.3','@U1.19'),('CARD1.1','NC'),
 ],
)
cfg['pcb']=dict(layers=4,
 netclasses={'Power':(0.20,0.127,0.6,0.3),'HighCurrent':(0.20,0.15,0.8,0.4),'USB':(0.25,0.127,0.6,0.3,0.28,0.18)},
 netclass_assign={**{n:'HighCurrent' for n in ['VBAT','VBAT_RAW','VSYS','VBUS','VSERVO','VSERVO_PRE','BQ_SW1','BQ_SW2','BUCK3V3_SW','BUCKSV_SW','PYRO1_OUT','PYRO2_OUT','U3_PMID']},
   **{n:'Power' for n in ['+3V3','+1V1_DVDD','+1V2_DSP','BQ_REGN','VREG_LX','GND','USB_OTP_VDD']},'USB_DP':'USB','USB_DN':'USB','USB_DM':'USB'},
 autoplace=[('U34','U18',('F','B')),('C35','U34',('F','B')),('C36','U34',('F','B')),('TP1','U1',('F','B'))],
)

cfg['pcb']['widen']={'HighCurrent':[1.5,1.2,1.0,0.8,0.6,0.5,0.4,0.3],'Power':[0.5,0.4,0.3,0.25],'USB':[0.28]}

cfg['pcb']['legacy']={'layers':[1,2,15,16]}
cfg['pcb']['in1_plane']=False
cfg['pcb']['fine_refs']=['U1','U3','U18','U2']
cfg['pcb']['hole_exempt']=['U17']

# =====================================================================================
# REV 3 (JLCPCBA release): electrical fixes + JLC/LCSC part assignment
# =====================================================================================
cfg['rev']='3.0'; cfg['date']='2026-10-03'
cfg['comment1']='Rev 3: JLCPCBA release (fixes: CH224K removed, BQ25798 PROG/TS/caps, buck EN/FB, RP2350 VREG/USB/XOSC/PSRAM CS, LEDs, INA226 addr)'
cfg['removed']=['U2','X1']
_x0,_y0=[2450],[-80]
def _pos():
    p=(_x0[0],_y0[0]); _y0[0]-=55
    if _y0[0]<-1950: _y0[0]=-80; _x0[0]+=170
    return p
_new=[]   # (ref, sym_from, value, lcsc, mpn, fp, {pin:net}, anchor)
def N(ref,sym,val,lcsc,mpn,fp,pins,anchor): _new.append((ref,sym,val,lcsc,mpn,fp,pins,anchor))
R402=('R14','R0402'); C402=('C1','C0402'); C805=('C7','C0805')
# ADAU1450 DVDD decoupling (one per DVDD pin 20/35/53/71)
for i,r in enumerate(['C37','C38','C39','C40']): N(r,*C402[:1],'100nF','C1525','CL05B104KO5NNNC',C402[1],{'1':'+1V2_DSP','2':'GND'},'U18')
# USB-C: CH224K removed -> plain 5.1k Rd sinks (5 V, up to 3 A advertised by source)
N('R40','R14','5.1k','C25905','0402WGF5101TCE','R0402',{'1':'USBC_CC1','2':'GND'},'USBC1')
N('R41','R14','5.1k','C25905','0402WGF5101TCE','R0402',{'1':'USBC_CC2','2':'GND'},'USBC1')
# RP2350 USB 27R series (RP2350 hardware design guide)
N('R42','R14','27','C25156','0402WGJ0270TCE','R0402',{'1':'USB_DP','2':'USB_DP_MCU'},'U1')
N('R43','R14','27','C25156','0402WGJ0270TCE','R0402',{'1':'USB_DN','2':'USB_DN_MCU'},'U1')
# BQ25798 TS bias (RT1 from REGN, RT2 to GND, NTC R1 to GND)
N('R44','R14','5.1k','C25905','0402WGF5101TCE','R0402',{'1':'BQ_REGN','2':'U3_TS'},'U3')
N('R45','R14','30k','C138008','RC0402FR-0730KL','R0402',{'1':'U3_TS','2':'GND'},'U3')
# BQ25798 power-path capacitors (datasheet 9.2.2: VBUS 2x10u+100n, PMID 3x10u, SYS 5x10u+100n, BAT 2x10u)
for r in ['C41','C42']: N(r,'C7','10uF','C15850','CL21A106KAYNNNE','C0805',{'1':'VBUS','2':'GND'},'U3')
N('C43','C1','100nF','C1525','CL05B104KO5NNNC','C0402',{'1':'VBUS','2':'GND'},'U3')
for r in ['C44','C45','C46']: N(r,'C7','10uF','C15850','CL21A106KAYNNNE','C0805',{'1':'U3_PMID','2':'GND'},'U3')
for r in ['C47','C48','C49']: N(r,'C7','10uF','C15850','CL21A106KAYNNNE','C0805',{'1':'VSYS','2':'GND'},'U3')
N('C50','C1','100nF','C1525','CL05B104KO5NNNC','C0402',{'1':'VSYS','2':'GND'},'U3')
for r in ['C51','C52']: N(r,'C7','10uF','C15850','CL21A106KAYNNNE','C0805',{'1':'VBAT','2':'GND'},'U3')
N('C53','C7','10uF','C15850','CL21A106KAYNNNE','C0805',{'1':'VSYS','2':'GND'},'U4')
N('C54','C7','10uF','C15850','CL21A106KAYNNNE','C0805',{'1':'VSYS','2':'GND'},'U5')
# buck output capacitors
for r in ['C55','C56']: N(r,'C7','22uF','C45783','CL21A226MAQNNNE','C0805',{'1':'+3V3','2':'GND'},'L2')
for r in ['C57','C58']: N(r,'C7','22uF','C45783','CL21A226MAQNNNE','C0805',{'1':'VSERVO_PRE','2':'GND'},'L3')
N('C59','C1','75pF','C107010','CC0402JRNPO9BN750','C0402',{'1':'VSERVO_PRE','2':'BUCKSV_FB'},'U5')
# RP2350 core regulator support (hardware design guide: 33R/4.7u AVDD filter, 4.7u VREG_VIN, 4.7u DVDD)
N('R46','R14','33','C25105','0402WGF330JTCE','R0402',{'1':'+3V3','2':'VREG_AVDD'},'U1')
N('C60','C1','4.7uF','C23733','CL05A475MP5NRNC','C0402',{'1':'VREG_AVDD','2':'GND'},'U1')
N('C61','C1','4.7uF','C23733','CL05A475MP5NRNC','C0402',{'1':'+3V3','2':'GND'},'U1')
N('C62','C1','4.7uF','C23733','CL05A475MP5NRNC','C0402',{'1':'+1V1_DVDD','2':'GND'},'L1')
# 12 MHz XOSC per reference design: ABM8-272-T3, 15 pF, 1k in XOUT
N('X1','X2','12MHz','C20625731','ABM8-272-T3','CRYSTAL-SMD_4P-L3.2-W2.5-BL',{'1':'XIN','2':'GND','3':'XOUT_X','4':'GND'},'U1')
N('R47','R14','1k','C11702','0402WGF1001TCE','R0402',{'1':'XOUT','2':'XOUT_X'},'X1')
# BOOTSEL button (QSPI_SS via 1k)
N('R48','R14','1k','C11702','0402WGF1001TCE','R0402',{'1':'QSPI_SS_FLASH','2':'BOOTSEL_SW'},'U6')
N('U35','U16','BOOTSEL','C2680625','EVQ-Q2P02W','SW-SMD_4P-L6.5-W6.0-P4.00-LS6.6-TL',{'1':'BOOTSEL_SW','3':'GND'},'U16')

for ref,sym,val,lcsc,mpn,fp,pins,anchor in _new:
    cfg['extra'].append(dict(ref=ref,sym_from=sym,sch=_pos(),mpn=mpn,lcsc=lcsc))
    cfg['values'][ref]=val; cfg['fp_override'][ref]=fp
    for pn,net in pins.items(): cfg['pin_fixes'].append((f'{ref}.{pn}',net))
    cfg['pcb']['autoplace'].append((ref,anchor,('F',)))
cfg['extra'][0]['lcsc']='C347218'; cfg['extra'][0]['mpn']='AMS1117-1.2'          # U34 UMW AMS1117-1.2
cfg['extra'][1]['lcsc']='C45783'; cfg['extra'][1]['mpn']='CL21A226MAQNNNE'       # C35
cfg['extra'][2]['lcsc']='C15850'; cfg['extra'][2]['mpn']='CL21A106KAYNNNE'       # C36
cfg['extra'][3]['lcsc']=''                                                       # TP1 bare pad, not assembled
cfg['pcb']['autoplace']=[a for a in cfg['pcb']['autoplace'] if a[0]!='X1']
cfg['pcb'].setdefault('place',{})
cfg['fp_override'].update({'L1':'L_Wuerth_PMFI-201610','L3':'L_Sunlord_SWPA6045S'})

cfg['pin_fixes']+= [
 # CH224K removed: CC pins to Rd resistors, GPIO42 freed
 ('USBC1.A5','USBC_CC1'),('USBC1.B5','USBC_CC2'),('U1.53','NC'),
 # USB pair: RP2350 side behind 27R
 ('U1.67','USB_DP_MCU'),('U1.66','USB_DN_MCU'),
 # PSRAM CS must be a QMI_CS1n-capable pin (GPIO0/8/19/47) -> GPIO47
 ('U1.58','PSRAM_CS'),('U1.42','U12_INT'),('U1.49','GPIO40_ADC0'),('U32.3','GPIO40_ADC0'),
 # VREG_AVDD through RC filter
 ('U1.61','VREG_AVDD'),
 # XOSC: C3 moves to crystal side of the 1k
 ('C3.1','XOUT_X'),
 # TPS563201 EN has an internal pull-down: tie to VIN (EN abs-max 19 V > VSYS)
 ('U4.5','VSYS'),
 # INA226 U9 to 0x41 (A0=VS); ALERT outputs left open
 ('U9.2','+3V3'),('U8.3','NC'),('U9.3','NC'),
 # LEDs were wired anode-to-GND: LED1 active-high from GPIO32, LED2 (charger STAT) fed from REGN
 ('LED1.1','@R9.2'),('LED1.2','GND'),('R8.2','BQ_REGN'),
]
cfg['netnames_by_pin']['R9.2']='LED1_A'
cfg['netnames_by_pin']['R8.1']='LED2_A'

cfg['pcb']['netclass_assign'].update({'USB_DP_MCU':'USB','USB_DN_MCU':'USB','VREG_AVDD':'Power','U3_PMID':'HighCurrent'})
cfg['pcb']['fine_refs']=['U1','U3','U18']

# ---------- JLC/LCSC assignment for original parts (value, LCSC, MPN). Passives moved to JLC Basic where one exists.
_B=dict
cfg['bom']={
 'C1':_B(value='100nF',lcsc='C1525',mpn='CL05B104KO5NNNC'),
 'C2':_B(value='15pF',lcsc='C1548',mpn='0402CG150J500NT'),'C3':_B(value='15pF',lcsc='C1548',mpn='0402CG150J500NT'),
 'C4':_B(value='18pF',lcsc='C1549',mpn='0402CG180J500NT'),'C5':_B(value='18pF',lcsc='C1549',mpn='0402CG180J500NT'),
 'C6':_B(value='1nF 50V',lcsc='C1523',mpn='0402B102K500NT'),
 'C7':_B(value='4.7uF 16V',lcsc='C19666',mpn='CL10A475KO8NNNC'),
 'C8':_B(value='150pF NP0',lcsc='C107038',mpn='CC0603JRNPO9BN151'),
 'C9':_B(value='5.6nF',lcsc='C281760',mpn='CC0402KRX7R9BB562'),
 'C10':_B(value='2200uF 25V',lcsc='C44598',mpn='KM228M025J20RR0VH2FP0'),
 'C17':_B(value='47nF 50V',lcsc='C82219',mpn='0402B473K500NT'),'C18':_B(value='47nF 50V',lcsc='C82219',mpn='0402B473K500NT'),
 'L1':_B(value='3.3uH',lcsc='C42411119',mpn='AOTA-B201610S3R3-101-T'),
 'L2':_B(value='2.2uH',lcsc='C5832372',mpn='FTC252012S2R2MBCA'),
 'L3':_B(value='10uH',lcsc='C79272',mpn='SWPA6045S100MT'),
 'L4':_B(value='2.2uH',lcsc='C602029',mpn='FHD4020S-2R2MT'),
 'R1':_B(value='10k NTC',lcsc='C13564',mpn='NCP18XH103F03RB'),
 'R2':_B(value='33k',lcsc='C25779',mpn='0402WGF3302TCE'),
 'R3':_B(value='10mΩ',lcsc='C158899',mpn='RTT03R010FTP'),'R7':_B(value='10mΩ',lcsc='C158899',mpn='RTT03R010FTP'),
 'R4':_B(value='47k',lcsc='C25792',mpn='0402WGF4702TCE'),'R5':_B(value='27k',lcsc='C25771',mpn='0402WGF2702TCE'),
 'R6':_B(value='20k',lcsc='C25765',mpn='0402WGF2002TCE'),
 'R8':_B(value='2.2k',lcsc='C25879',mpn='0402WGF2201TCE'),
 'R9':_B(value='330',lcsc='C25104',mpn='0402WGF3300TCE'),
 'R10':_B(value='4.3k',lcsc='C23159',mpn='0603WAF4301T5E'),
 'R11':_B(value='1k',lcsc='C11702',mpn='0402WGF1001TCE'),'R13':_B(value='1k',lcsc='C11702',mpn='0402WGF1001TCE'),
 'R12':_B(value='8.2k',lcsc='C25981',mpn='0603WAF8201T5E'),
 'R16':_B(value='33k',lcsc='C25779',mpn='0402WGF3302TCE'),'R18':_B(value='33k',lcsc='C25779',mpn='0402WGF3302TCE'),
 'R31':_B(value='10k',lcsc='C25744',mpn='0402WGF1002TCE'),'R32':_B(value='10k',lcsc='C25744',mpn='0402WGF1002TCE'),
 'U6':_B(value='W25Q128JVSIQ',lcsc='C97521',mpn='W25Q128JVSIQ'),
}
for r in ['C11','C12','C13','C14','C16','C19','C20','C21','C22','C23','C24','C25','C26','C27','C28','C29','C30','C31','C32','C33']:
    cfg['bom'][r]=_B(value='100nF',lcsc='C1525',mpn='CL05B104KO5NNNC')
for r in ['R14','R15','R17','R19','R20']: cfg['bom'][r]=_B(value='10k',lcsc='C25744',mpn='0402WGF1002TCE')
for r in ['R36','R37','R38','R39']: cfg['bom'][r]=_B(value='4.7k',lcsc='C25900',mpn='0402WGF4701TCE')
cfg['dnp']=['TP1']
cfg['bom']['C23']=_B(value='10nF',lcsc='C15195',mpn='CL05B103KB5NNNC')   # LSM9DS1 CAP pin: 10 nF per ST datasheet sec. 4.1

# ---------- extra local decoupling (one 100 nF per IC supply pin group that had none)
_dec=[('C63','U6.8'),('C64','U7.8'),('C65','U10.10'),('C66','U11.8'),('C67','U13.5'),('C68','U14.22'),('C69','U14.1'),
      ('C70','U15.3'),('C71','U15.28'),('C72','U12.18'),('C73','U17.1'),('C75','U8.6'),('C76','U9.6'),
      ('C77','U18.2'),('C78','U18.18'),('C79','U18.38'),('C80','U18.56'),('C81','U18.7'),('C82','U18.15')]
for r,pin in _dec:
    _new.append((r,'C1','100nF','C1525','CL05B104KO5NNNC','C0402',{'1':'+3V3','2':'GND'},pin.split('.')[0]))
_new.append(('C74','C7','10uF','C15850','CL21A106KAYNNNE','C0805',{'1':'+3V3','2':'GND'},'CARD1'))
for ref,sym,val,lcsc,mpn,fp,pins,anchor in _new[-20:]:
    cfg['extra'].append(dict(ref=ref,sym_from=sym,sch=_pos(),mpn=mpn,lcsc=lcsc))
    cfg['values'][ref]=val; cfg['fp_override'][ref]=fp
    for pn,net in pins.items(): cfg['pin_fixes'].append((f'{ref}.{pn}',net))

# ---------- floorplan (rev 3): connectors/holes keep their EasyEDA positions, functional blocks re-placed,
# every passive auto-placed next to the pin it serves (anchor table below, else first IC pad on its net)
cfg['pcb']['floorplan']=dict(
 keep=['USBC1','U16','U22','H1','CN1','U12','CARD1','C10','Q1','Q2','U19','U20','U21','U23','U24','U25','U26','U27','U28','U29','U30','U31','U32','U33'],
 fixed={ # ref: (x, y, rot)
  'U1':(97,92,90),
  'U3':(80,77,270),'L4':(80,70.5,0),
  'U4':(93,79.5,0),'L2':(97.5,79.5,90),
  'U18':(114,88,-90),'X2':(106.8,82.5,0),'U34':(114.5,77.5,0),'U17':(121.5,100,0),
  'U5':(75,95,0),'L3':(75.5,102,0),'U9':(83,104,0),
  'U6':(84.5,94,90),'U7':(86.5,86.5,0),'L1':(88.6,87.5,90),
  'X1':(106,93,0),
  'U15':(108,104.5,0),'U14':(102.5,107.5,0),'U13':(111.5,99,0),'U10':(97.5,108,0),'U11':(108,111,0),
  'U8':(71.5,89,90),'U35':(86,63.5,0),
 },
 anchors={
  'C1':'U1.5','C16':'U1.15','C26':'U1.24','C27':'U1.29','C28':'U1.41','C29':'U1.50','C30':'U1.60','C31':'U1.76','C32':'U1.59','C33':'U1.68',
  'C11':'U1.10','C12':'U1.32','C13':'U1.51','C14':'L1.2','C62':'L1.2','C61':'U1.64','C60':'U1.61','R46':'U1.61',
  'C37':'U18.20','C38':'U18.35','C39':'U18.53','C40':'U18.71','C35':'U34.2','C36':'U34.3',
  'C20':'U4.6','C53':'U4.3','C55':'L2.2','C56':'L2.2','R2':'U4.4','R31':'U4.4',
  'C21':'U5.6','C54':'U5.3','C57':'L3.2','C58':'L3.2','C59':'U5.4','R4':'U5.4','R5':'U5.4','R32':'U5.4','R7':'U9.10',
  'C41':'U3.2','C42':'U3.3','C43':'U3.8','C44':'U3.29','C45':'U3.29','C46':'U3.29','C19':'U3.29','C47':'U3.25','C48':'U3.25','C49':'U3.25','C50':'U3.25',
  'C51':'U3.22','C52':'U3.23','C7':'U3.5','C17':'U3.4','C18':'U3.19','C6':'U3.24','R12':'U3.20','R44':'U3.16','R45':'U3.16','R1':'U3.16','R8':'U3.1','LED2':'U3.1',
  'R3':'CN1.2','C8':'U18.16','C9':'U18.16','R10':'U18.16','C4':'U18.22','C5':'U18.21',
  'C2':'X1.1','C3':'X1.3','R47':'U1.31','R42':'U1.67','R43':'U1.66','R40':'USBC1.A5','R41':'USBC1.B5',
  'R48':'U6.1','R17':'U1.35','TP1':'U1.33','R9':'U1.40','LED1':'R9.2','R36':'U1.11','R37':'U1.12','R38':'U1.13','R39':'U1.14','R6':'CARD1.9',
  'C22':'U13.4','C23':'U14.21','C24':'U14.24','C25':'U15.9',
 },
 order_first=['C11','C12','C13','C14','C62','C61','C60','R46','R42','R43','R47','C2','C3','C37','C38','C39','C40','C17','C18','C7','C6','C41','C42','C43','C44','C45','C46','C19','C47','C48','C49','C50','C51','C52','R12','C20','C21','C53','C54','C55','C56','C57','C58','C4','C5','C8','C9','R10'],
 margin=0.4,
)
cfg['pcb']['autoplace']=[]
cfg['pcb']['floorplan']['anchors'].update({r:p for r,p in _dec})
cfg['pcb']['floorplan']['anchors'].update({'C74':'CARD1.4','R11':'Q1.1','R14':'Q1.1','R13':'Q2.1','R20':'Q2.1','R16':'U21.2','R18':'U33.2','R15':'U12.12','R19':'U12.13','D2':'U12.12','D1':'U12.13'})
cfg['pcb']['legacy']=None
cfg['pcb']['floorplan']['fixed'].update({'U7':(84,86,0),'X2':(105.8,82.5,0),'U22':(122.2,113,0)})
cfg['pcb']['floorplan']['keep'].remove('U22')
cfg['pcb']['floorplan']['keepout']={'MH1':0.6,'MH2':0.6,'MH3':0.6,'MH4':0.6}
cfg['pcb']['floorplan']['fixed'].update({'D1':(112.3,126.5,90),'D2':(112.3,122.0,90)})
for k in ('D1','D2'): cfg['pcb']['floorplan']['anchors'].pop(k,None)
cfg['pcb']['floorplan']['fixed'].update({'D1':(112.0,127.0,90),'D2':(112.0,121.5,90)})
cfg['pcb']['in1_plane']=True
# rev 3 routing density: 0.5/0.3 mm signal vias (JLC standard, no surcharge), escape ring around the fine-pitch ICs
cfg['pcb']['default_via']=(0.5,0.3)
cfg['pcb']['netclasses']={'Power':(0.20,0.127,0.5,0.3),'HighCurrent':(0.20,0.15,0.8,0.4),'USB':(0.25,0.127,0.5,0.3,0.28,0.18)}
cfg['pcb']['floorplan']['keepout'].update({'U1':1.3,'U18':1.0,'U3':0.7})
# rev 3: deterministic U1 fanout (stub + 0.5/0.3 via per pin, alternating in/out) so no pin gets boxed in
cfg['pcb']['qfn_fanout']={'U1':{'exclude':['62','63','64','65','66','67','30','31']}}

# ---------- rev 3: bootstrap caps were cross-wired in the original schematic (BTST1 must sit on SW1, BTST2 on SW2: BQ25798 DS pin table)
cfg['pin_fixes']+=[('C17.2','BQ_SW1'),('C18.2','BQ_SW2')]

# ---------- rev 3: hand-placed BQ25798 power stage (TI EVM style): L4 straight above the PMID/SW1/GND/SW2/SYS bars,
# PMID caps to the left, SYS caps to the right, VBUS/BAT caps below them, power loop pre-routed and locked.
_X,_Y=80.0,79.0
cfg['pcb']['floorplan']['fixed'].update({
 'U3':(_X,_Y,0),'L4':(_X,_Y-6.0,180),
 'C44':(_X-4.4,_Y-3.1,180),'C45':(_X-4.4,_Y-4.9,180),'C46':(_X-4.4,_Y-6.7,180),
 'C47':(_X+4.4,_Y-2.8,0),'C48':(_X+4.4,_Y-4.6,0),'C49':(_X+4.4,_Y-6.4,0),
 'C41':(_X-5.1,_Y-1.1,180),'C42':(_X-5.1,_Y+0.7,180),
 'C51':(_X+4.4,_Y-0.4,0),'C52':(_X+4.4,_Y+1.4,0),
})
for k in ('C44','C45','C46','C47','C48','C49','C41','C42','C51','C52'): cfg['pcb']['floorplan']['anchors'].pop(k,None)
_bt=_Y-1.725+0.5   # bar tips (y of the end nearest the inductor) = _Y-2.225
_t=_Y-2.225
cfg['pcb']['preroute_geom']=dict(tracks=[
 # PMID: bar -> left -> vertical bus through C44/C45/C46 pad 1
 ('U3_PMID',[(_X-0.90,_t),(_X-1.40,_t-0.58),(_X-3.4,_t-0.58)],0.4),
 ('U3_PMID',[(_X-3.4,_Y-3.1),(_X-3.4,_Y-6.7)],0.8),
 # SW1 -> L4 pad 2 (left after 180 deg)
 ('BQ_SW1',[(_X-0.45,_t),(_X-0.45,_t-0.78)],0.3),
 ('BQ_SW1',[(_X-0.45,_t-0.78),(_X-1.10,_t-1.43),(_X-1.10,_t-2.3)],0.35),
 # GND bar -> vias under L4 (between its pads)
 ('GND',[(_X,_t),(_X,_Y-6.7)],0.3),
 # SW2 -> L4 pad 1 (right)
 ('BQ_SW2',[(_X+0.45,_t),(_X+0.45,_t-0.78)],0.3),
 ('BQ_SW2',[(_X+0.45,_t-0.78),(_X+1.10,_t-1.43),(_X+1.10,_t-2.3)],0.35),
 # SYS: bar -> right -> vertical bus through C47/C48/C49 pad 1
 ('VSYS',[(_X+0.90,_t),(_X+1.40,_t-0.58),(_X+3.4,_t-0.58)],0.4),
 ('VSYS',[(_X+3.4,_Y-2.8),(_X+3.4,_Y-6.4)],0.8),
 # GND star under the package (no exposed pad on RQM): bar 27 bottom end and pins 10/11/13 inward to two vias
 ('GND',[(_X,_Y-1.225),(_X,_Y+0.2)],0.25),
 ('GND',[(_X-1.0,_Y+1.575),(_X-0.8,_Y+0.9)],0.2),
 ('GND',[(_X-0.6,_Y+1.575),(_X-0.8,_Y+0.9)],0.2),
 ('GND',[(_X+0.2,_Y+1.575),(_X+0.2,_Y+0.9),(_X,_Y+0.2)],0.2),
],vias=[('GND',_X,_Y-4.7,0.6,0.3),('GND',_X,_Y-5.7,0.6,0.3),('GND',_X,_Y-6.7,0.6,0.3),
        ('GND',_X,_Y+0.2,0.5,0.3),('GND',_X-0.8,_Y+0.9,0.5,0.3)])
cfg['pcb']['floorplan']['fixed'].update({
 'C44':(_X-4.8,_Y-2.9,180),'C45':(_X-4.8,_Y-4.9,180),'C46':(_X-4.8,_Y-6.9,180),
 'C47':(_X+4.8,_Y-2.9,0),'C48':(_X+4.8,_Y-4.9,0),'C49':(_X+4.8,_Y-6.9,0),
 'C41':(_X-4.8,_Y-0.9,180),'C42':(_X-4.8,_Y+1.1,180),
 'C51':(_X+4.8,_Y-0.9,0),'C52':(_X+4.8,_Y+1.1,0)})
_tr=cfg['pcb']['preroute_geom']['tracks']
_tr[0]=('U3_PMID',[(_X-0.90,_t),(_X-1.40,_t-0.58),(_X-3.8,_t-0.58)],0.4)
_tr[1]=('U3_PMID',[(_X-3.8,_Y-2.9),(_X-3.8,_Y-6.9)],0.8)
_tr[7]=('VSYS',[(_X+0.90,_t),(_X+1.40,_t-0.58),(_X+3.8,_t-0.58)],0.4)
_tr[8]=('VSYS',[(_X+3.8,_Y-2.9),(_X+3.8,_Y-6.9)],0.8)
_tr[3]=('BQ_SW1',[(_X-0.45,_t-0.78),(_X-1.10,_t-1.43),(_X-1.10,_t-2.3)],0.3)
_tr[6]=('BQ_SW2',[(_X+0.45,_t-0.78),(_X+1.10,_t-1.43),(_X+1.10,_t-2.3)],0.3)
# rev 3 routing rules: signals at 0.1/0.1 mm (JLC multilayer standard capability is 0.09/0.09 mm),
# widened back to 0.15 mm wherever room allows; no forced QFN fanout (it fenced the inner layers)
cfg['pcb'].pop('qfn_fanout',None)
cfg['pcb'].update(default_track=(0.1,0.1),min_track=0.1,min_clear=0.1,gr_clr=0.11,gr_tw=0.1,gr_fine_zones=[(50,50,150,150)],gr_fine_clr=0.105)
cfg['pcb']['widen']['Default']=[0.15,0.127]
# final routing recipe: In1 routable (GND poured on F/B/In1 afterwards), FR at 0.15/0.127, repair at 0.1/0.1
cfg['pcb']['in1_plane']=False
cfg['pcb'].update(default_track=(0.15,0.127),min_track=0.1,min_clear=0.1)
cfg['pcb']['extra_dru']="(rule \"Signal fine 3.9mil\" (condition \"A.NetClass == 'Default' && B.NetClass == 'Default'\") (constraint clearance (min 0.1mm)))\n"
# ---------- rev 3: GPIO pin swap. Every freely-assignable GPIO function (header, servo, aux, interrupts, PIO audio,
# LED, card-detect) re-assigned to the RP2350B pin nearest its destination (Hungarian assignment on pad distance,
# total wirelength 1001 mm -> 769 mm). Nets renamed by function; firmware pin map is generated from the netlist.
import json as _json
_ps=_json.load(open('pinswap_r3.json'))
cfg['pin_fixes']+= [tuple(x) for x in _ps['fixes']]
# rev 3: BQ25798 D+/D- left open. The USB pair now runs point-to-point USB-C <-> RP2350 (no stub to the charger);
# firmware sets IINDPM over I2C and clears AUTO_INDET_EN, so BC1.2 detection is not needed.
cfg['pin_fixes']+=[('U3.6','NC'),('U3.7','NC')]
cfg['bom']['X2']=dict(value='12.288MHz',lcsc='C519811',mpn='NX3225GA-12.288MHZ-STD-CRG-2')
