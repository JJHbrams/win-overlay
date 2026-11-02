"""Semantic review ownership; names such as DentalCrowns are not hair."""
LEGACY_HAIR_OWNERS=frozenset({
 'MIA_V17_PIXAL_DetailedHair','MIA_V20_Crown_PixalDonorLock',
 'MIA_V17_LeftBraid_Tail','MIA_V17_LeftBraid_Lane0','MIA_V17_LeftBraid_Lane1','MIA_V17_LeftBraid_Lane2','MIA_V17_LeftBraid_Tie',
 'MIA_V17_RootLining_MIA_V06_BODY_SKIN','MIA_V17_RootLining_MIA_V14_SculptedSkin',
 'MIA_V24_Gather_Main','MIA_V24_Gather_Tuck','MIA_V24_Gather_Upper'})

def is_hair_object(ob):
 if ob.get('mia_component')=='mouth' or 'DentalCrowns' in ob.name:return False
 return ob.get('mia_component')=='hair' or ob.name in LEGACY_HAIR_OWNERS
