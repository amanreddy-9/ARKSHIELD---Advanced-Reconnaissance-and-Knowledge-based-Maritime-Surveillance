"""Evaluate existing classifier on the two labeled held-out class directories."""
from pathlib import Path
import json,time,argparse
import torch
from PIL import Image
from models.classifier import ShipClassifier

torch.set_num_threads(4)
parser=argparse.ArgumentParser();parser.add_argument('--output',default='labeled_pair_evaluation.json');args=parser.parse_args()
root=Path(Path('outputs/diagnostics/current_complete_audit.txt').read_text())
c=ShipClassifier();rows=[];partial=[];start=time.monotonic()
for label in ['Frigate','Destroyer']:
 files=sorted(p for p in (Path('data/TITANIC-FGS-10/ImageNet/test')/label).iterdir() if p.suffix.lower() in ['.jpg','.jpeg','.png','.bmp'])
 for offset in range(0,len(files),16):
  batch=files[offset:offset+16];images=[Image.open(f).convert('RGB') for f in batch]
  with torch.no_grad():probs=c.model(torch.stack([c.transform(im) for im in images]).to(c.device)).softmax(1).cpu().numpy()
  for f,im,p in zip(batch,images,probs):
   order=p.argsort()[::-1];rows.append(dict(path=str(f),ground_truth=label,prediction=c.CLASS_NAMES[order[0]],top2=c.CLASS_NAMES[order[1]],frigate=float(p[c.CLASS_NAMES.index('Frigate')]),destroyer=float(p[c.CLASS_NAMES.index('Destroyer')]),margin=float(p[order[0]]-p[order[1]]),probabilities={name:float(v) for name,v in zip(c.CLASS_NAMES,p)}))
   if sum(r['ground_truth']==label for r in partial)<12:
    crop=im.crop((int(im.width*.2),0,int(im.width*.8),im.height));r=c.classify(crop,use_vlm_disambiguation=False);partial.append(dict(path=str(f),ground_truth=label,**r))
  print(label,offset+len(batch),'/',len(files),flush=True)
summary={label:dict(samples=sum(r['ground_truth']==label for r in rows),correct=sum(r['ground_truth']==label and r['prediction']==label for r in rows),confused_as_other=sum(r['ground_truth']==label and r['prediction']==({'Frigate':'Destroyer','Destroyer':'Frigate'}[label]) for r in rows)) for label in ['Frigate','Destroyer']}
with (root/args.output).open('x',encoding='utf-8') as f: json.dump(dict(summary=summary,samples=rows,partial_visibility=partial,seconds=time.monotonic()-start,class_names=c.CLASS_NAMES,device=str(c.device),evaluation_mode=not c.model.training),f,indent=2)
print(json.dumps(summary),flush=True)
