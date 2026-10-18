import subprocess,sys,os
from PIL import Image
def run(*a): subprocess.run(list(a),capture_output=True)
def renders(out,name):
    pcb=f'{out}/{name}.kicad_pcb'; d=f'{out}/renders'; os.makedirs(d,exist_ok=True)
    sets={'top':'F.Cu,F.SilkS,F.Mask,Edge.Cuts','bottom':'B.Cu,B.SilkS,B.Mask,Edge.Cuts','in1':'In1.Cu,Edge.Cuts','in2':'In2.Cu,Edge.Cuts','all_copper':'F.Cu,In1.Cu,In2.Cu,B.Cu,Edge.Cuts'}
    for k,l in sets.items():
        extra=['--mirror'] if k=='bottom' else []
        run('kicad-cli','pcb','export','svg','--mode-single','--layers',l,'--page-size-mode','2','--exclude-drawing-sheet',*extra,'-o',f'{d}/{k}.svg',pcb)
        run('rsvg-convert','-b','white','-w','2000',f'{d}/{k}.svg','-o',f'{d}/{name}_{k}.png'); os.remove(f'{d}/{k}.svg')
    for side in ('top','bottom'):
        run('kicad-cli','pcb','render','--side',side,'--width','2000','--height','2000','--quality','basic','--background','opaque','-o',f'{d}/{name}_3d_{side}.png',pcb)
    run('kicad-cli','pcb','export','pdf','--mode-multipage','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,Edge.Cuts','-o',f'{out}/{name}_layers.pdf',pcb)
    run('kicad-cli','sch','export','pdf','-o',f'{out}/{name}_schematic.pdf',f'{out}/{name}.kicad_sch')
if __name__=='__main__': renders(sys.argv[1],sys.argv[2])
