from pathlib import Path
base=Path(__file__).resolve().parent.parent/'export_scope_and_sections.py'
source=base.read_text().replace('H=OUT.parent;SOURCE=', 'H=OUT.parent.parent;SOURCE=').replace("TARGET=OUT/'Mia_FaceFinish7_MalarVolumeR25_v22.blend'","TARGET=OUT/'Mia_FaceFinish7_OrbitalTransitionR27_v22.blend'").replace("OUT/'baseline-volume-inspection.json'","OUT.parent/'baseline-volume-inspection.json'").replace("'r25_y':y","'r27_y':y")
expanded=Path(__file__).with_name('expanded-export.py');expanded.write_text(source);exec(compile(source,str(expanded),'exec'))
