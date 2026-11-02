"""Read-only Mia working-file inventory. Never follow junctions into other volumes."""
from pathlib import Path
import argparse, collections, json, os, subprocess
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--tag',required=True)
a=ap.parse_args();repo=Path(a.repo).resolve();root=repo/'asset/mia'
tracked=set(p.lower().replace('\\','/') for p in subprocess.check_output(['git','ls-files','-z'],cwd=repo).decode('utf-8').split('\0') if p)
rows=[];skipped=[];errors=[];stack=[root]
while stack:
 folder=stack.pop()
 try: entries=list(os.scandir(folder))
 except OSError as e:errors.append([str(folder),str(e)]);continue
 for entry in entries:
  path=Path(entry.path)
  try:
   if entry.is_symlink() or (hasattr(os.path,'isjunction') and os.path.isjunction(path)):
    skipped.append(str(path));continue
   if entry.is_dir(follow_symlinks=False):stack.append(path);continue
   if not entry.is_file(follow_symlinks=False):continue
   st=entry.stat(follow_symlinks=False);rel=path.relative_to(repo).as_posix()
   rows.append(dict(path=str(path),relative=rel,bytes=st.st_size,extension=path.suffix.lower(),tracked=rel.lower() in tracked,
                    inode=[st.st_dev,st.st_ino],mtime=st.st_mtime))
  except OSError as e:errors.append([str(path),str(e)])
groups=collections.Counter();ext=collections.Counter();status=collections.Counter()
for r in rows:
 parts=Path(r['relative']).parts;group='/'.join(parts[:5]);groups[group]+=r['bytes'];ext[r['extension']]+=r['bytes'];status['tracked' if r['tracked'] else 'untracked']+=r['bytes']
report=dict(repo=str(repo),meaning='Logical bytes of physical C files; junctions/symlinks excluded. NTFS compression/allocation may differ.',total_bytes=sum(r['bytes'] for r in rows),files=len(rows),
   by_group=groups.most_common(),by_extension=ext.most_common(),by_tracking=dict(status),largest=sorted(rows,key=lambda r:r['bytes'],reverse=True)[:120],
   skipped=skipped,errors=errors,all_files=rows)
out=P/'storage';out.mkdir(exist_ok=True);f=out/(a.tag+'.json');f.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['repo','total_bytes','files','by_tracking','by_extension','skipped','errors']},indent=2))
print('TOP_GROUPS',json.dumps(report['by_group'][:18]));print('TOP_FILES',json.dumps([{k:r[k] for k in ['relative','bytes','tracked']} for r in report['largest'][:12]]))
