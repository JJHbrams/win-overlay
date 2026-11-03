from pathlib import Path
MIA_LIVE_EXPORT_REVISION = 'live-E'
path = Path('D:/MiaWorkCache/mia-reference-work/win-overlay/tools/mia/review_h/live_export.py')
exec(compile(path.read_text(encoding='utf8'), str(path), 'exec'))
