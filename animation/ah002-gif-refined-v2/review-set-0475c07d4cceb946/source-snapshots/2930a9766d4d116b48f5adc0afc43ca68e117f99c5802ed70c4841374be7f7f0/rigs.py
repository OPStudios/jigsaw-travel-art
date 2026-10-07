"""Bind one reviewed scene decision to original painted pixels."""
from __future__ import annotations
from PIL import Image
from actions import RigidPlant,Steam,StableFloat,RigidDrift,SurfaceFlow,Insect,ChimneySmoke

def prepare(image,physical,original_size):
    action=physical['action']
    if action=='fixed_solid':return image,None,(0,0),{}
    if action=='continuous_emission':
        actor=ChimneySmoke(image) if physical.get('emissionMaterial')=='dense_locomotive_smoke' else Steam(image)
        return image,actor,(0,0),{}
    if action in ['reflection_flow','flame_flow']:
        return image,SurfaceFlow(image,'flame' if action=='flame_flow' else 'water',physical.get('texturePhase',0)),(0,0),{}
    pad=40;padded=Image.new('RGBA',(image.width+pad*2,image.height+pad*2));padded.alpha_composite(image,(pad,pad))
    anchor=[pad+physical['anchorNormalized'][a]*image.size[a] for a in range(2)]
    metadata={'anchorPx':anchor}
    if action in ['rooted_rigid','hanging_rigid']:
        actor=RigidPlant(padded,anchor,physical.get('maximumDegrees',.8),physical.get('delaySeconds',.5))
    elif action=='rigid_float':actor=StableFloat(padded,physical.get('floatPhase',0))
    elif action in ['rigid_glide','cloud_drift']:actor=RigidDrift(padded,physical['velocity'])
    elif action=='anatomical_insect':
        scale=lambda point:[pad+point[a]*image.size[a]/original_size[a] for a in range(2)]
        polygons=lambda rows:[[scale(point) for point in polygon] for polygon in rows]
        joint=scale(physical['jointPx']);axis=[physical['bodyAxis'][a]*image.size[a]/original_size[a] for a in range(2)]
        actor=Insect(padded,axis,joint,physical.get('bodyRadius',0)*image.width/original_size[0],physical.get('species','butterfly'),polygons(physical['bodyPolygons']),polygons(physical['wingPolygons']),physical.get('wingSides'))
        metadata['anatomicalMasks']={'body':actor.body,**{f'wing-{i+1}':wing[0] for i,wing in enumerate(actor.wings)}}
    else:raise ValueError('Unreviewed action '+action)
    return padded,actor,(-pad,-pad),metadata
