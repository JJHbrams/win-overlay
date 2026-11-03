from pathlib import Path
MIA_LIVE_EXPORT_REVISION = 'live-E'
path = Path(__file__).with_name('live_export.py')
exec(compile(path.read_text(encoding='utf8'), str(path), 'exec'))
