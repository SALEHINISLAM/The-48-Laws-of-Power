# pass 1: ben on full page (TSV). pass 2: Bengali-script model on lines with weak words -> bsc.tsv with same coordinates
import tesserocr, sys, os, csv, io
from PIL import Image
P='/usr/share/tesseract-ocr/5/tessdata/'
files=[l.strip() for l in open('list.txt')]
k,n=int(sys.argv[1]),int(sys.argv[2])
ben=tesserocr.PyTessBaseAPI(path=P,lang='ben',psm=tesserocr.PSM.SINGLE_COLUMN)
bsc=tesserocr.PyTessBaseAPI(path=P,lang='Bengali',psm=tesserocr.PSM.SINGLE_LINE)
import re
LAT=re.compile('[A-Za-z|৷]')
for f in files[k::n]:
    b=os.path.splitext(os.path.basename(f))[0]
    if os.path.exists(f'ocr/{b}.bsc.tsv'): continue
    im=Image.open(f).convert('L'); im=im.resize((im.width*2,im.height*2),Image.LANCZOS)
    if not os.path.exists(f'ocr/{b}.ben.tsv'):
        ben.SetImage(im); ben.Recognize(); open(f'ocr/{b}.ben.tsv','w').write(ben.GetTSVText(0))
    rows=[r for r in csv.reader(open(f'ocr/{b}.ben.tsv'),delimiter='\t',quoting=csv.QUOTE_NONE) if len(r)>=12 and r[0]=='5']
    lines={}
    for r in rows:
        lines.setdefault((r[2],r[3],r[4]),[]).append(r)
    out=[]
    for key,ws in lines.items():
        if not any(float(w[10])<90 or LAT.search(w[11]) for w in ws): continue
        x=min(int(w[6]) for w in ws); y=min(int(w[7]) for w in ws)
        x2=max(int(w[6])+int(w[8]) for w in ws); y2=max(int(w[7])+int(w[9]) for w in ws)
        pad=12; box=(max(0,x-pad),max(0,y-pad),min(im.width,x2+pad),min(im.height,y2+pad))
        bsc.SetImage(im.crop(box)); bsc.Recognize()
        for r in csv.reader(io.StringIO(bsc.GetTSVText(0)),delimiter='\t',quoting=csv.QUOTE_NONE):
            if len(r)>=12 and r[0]=='5' and r[11].strip():
                r[2]='900'; r[6]=str(int(r[6])+box[0]); r[7]=str(int(r[7])+box[1])
                out.append('\t'.join(r))
    open(f'ocr/{b}.bsc.tsv','w').write('\n'.join(out)+'\n')
    print(b,flush=True)
