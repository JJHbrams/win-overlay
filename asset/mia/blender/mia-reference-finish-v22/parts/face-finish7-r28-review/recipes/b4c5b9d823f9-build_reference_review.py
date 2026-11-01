from pathlib import Path
base=Path(__file__).resolve().parents[2]/'candidate-r25/refinement-r27/review-package/build_reference_review.py'
source=base.read_text().replace('R27','R28').replace('H=R28.parent.parent','H=R28.parent')
source=source.replace('source-r23-r27','source-r23-r28')
source=source.replace('WORKING BASE ONLY - NOT ART PASS','WORKING CANDIDATE / ART UNAPPROVED').replace('LOCAL RESTORED-VOLUME CANDIDATE / WORKING BASE ONLY; NOT ART PASS; not adopted','WORKING CANDIDATE / ART UNAPPROVED; AC-SURFACE FAIL; not adopted')
source=source.replace('R28 is an unaccepted working base.','R28 is an unapproved working candidate. Medial transition modestly softer than R27, but independent AC-SURFACE remains FAIL.')
expanded=Path(__file__).with_name('expanded-composer.py');expanded.write_text(source);exec(compile(source,str(expanded),'exec'))
