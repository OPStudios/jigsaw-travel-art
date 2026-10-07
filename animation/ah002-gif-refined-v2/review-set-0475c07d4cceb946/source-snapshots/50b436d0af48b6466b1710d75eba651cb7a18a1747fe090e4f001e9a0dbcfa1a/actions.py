"""Inspected two-scene physical actions. These functions move existing pixels only."""
from __future__ import annotations

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def smooth(x):
    return np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))


def bilinear(array, x, y, wrap_y=False):
    height, width = array.shape[:2]
    x = np.clip(x, 0, width - 1)
    y = np.mod(y, height) if wrap_y else np.clip(y, 0, height - 1)
    x0, y0 = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32)
    x1 = np.minimum(x0 + 1, width - 1)
    y1 = (y0 + 1) % height if wrap_y else np.minimum(y0 + 1, height - 1)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    return ((array[y0, x0] * (1-fx) + array[y0, x1] * fx) * (1-fy)
            + (array[y1, x0] * (1-fx) + array[y1, x1] * fx) * fy)


def affine(image, matrix, pivot, translation=(0, 0)):
    """Project a selected rigid component about its measured physical hinge."""
    matrix = np.asarray(matrix, dtype=np.float64)
    inv = np.linalg.inv(matrix)
    pivot = np.asarray(pivot, dtype=np.float64)
    offset = pivot - inv @ (pivot + np.asarray(translation))
    return image.transform(image.size, Image.Transform.AFFINE,
                           (*inv[0], offset[0], *inv[1], offset[1]),
                           Image.Resampling.BICUBIC)


def rotation(degrees):
    angle = math.radians(degrees)
    return np.array([[math.cos(angle), -math.sin(angle)],
                     [math.sin(angle), math.cos(angle)]])


def gust(time, delay=0):
    """One directional gust with unequal downstream responses; no forced reset."""
    t = time - delay
    return (math.exp(-((t-.95)/.62)**2) - .18*math.exp(-((t-2.05)/.70)**2))


class RigidPlant:
    def __init__(self, image, anchor, strength, delay, joint=None, stiffness=.45):
        self.image = image
        self.anchor = anchor
        self.strength, self.delay = strength, delay
        self.joint, self.stiffness = joint, stiffness
        if joint is not None:
            # The seam is deliberately placed on a narrow source stem, not on
            # leaf blades. Upper/lower components remain rigid independently.
            y = np.arange(image.height)[:, None]
            upper = (y < joint[1]).astype(np.float32)
            self.upper = image.copy()
            self.upper.putalpha(Image.fromarray(np.uint8(np.asarray(image.getchannel('A')) * upper)))
            self.lower = image.copy()
            self.lower.putalpha(Image.fromarray(np.uint8(np.asarray(image.getchannel('A')) * (1-upper))))

    def frame(self, time):
        if time<=0:return self.image.copy()
        entry=float(smooth(time/.30))
        angle = self.strength * gust(time, self.delay) * entry
        first = rotation(angle)
        if self.joint is None:
            return affine(self.image, first, self.anchor)
        lower = affine(self.lower, first, self.anchor)
        # Distal response lags the base. It is a second hinge, not a sheet warp.
        distal = self.strength*self.stiffness*gust(time, self.delay+.16) * entry
        upper = affine(self.upper, rotation(distal), self.joint)
        upper = affine(upper, first, self.anchor)
        lower.alpha_composite(upper)
        return lower


class Steam:
    def __init__(self, image):
        self.image = image
        raw = np.asarray(image).astype(np.float32)/255
        raw[:, :, :3] *= raw[:, :, 3:4]
        self.raw = raw
        self.y, self.x = np.mgrid[:image.height, :image.width].astype(np.float32)
        self.height = image.height

    def frame(self, time):
        if time<=0:return self.image.copy()
        # Continuous material transport. Density enters at the cup, travels up,
        # curls downwind, and dissipates near the top. No plume resurrection.
        height, width = self.image.height, self.image.width
        above = (height - 1 - self.y) / max(1, height - 1)
        source_y = self.y + time * 36
        curl = above * (4.2*np.sin(above*7-time*1.4) + 2.0*np.sin(above*13-time*2.0))
        first = bilinear(self.raw, self.x-curl-2.2*time*above, source_y, wrap_y=True)
        second = bilinear(self.raw, self.x-curl*.65+3.5*above, source_y+height*.43, wrap_y=True)
        transported = first*.78 + second*.34
        # The bottom attachment is a steady narrow source. It does not slide
        # or go dark when an old upper wisp leaves the frame.
        source_blend = smooth((above-.02)/.18)[..., None]
        transported = self.raw*(1-source_blend) + transported*source_blend
        dissipate = smooth(self.y/max(1,height*.32))[..., None]
        transported *= dissipate
        entry=float(smooth(time/.28))
        transported=self.raw*(1-entry)+transported*entry
        alpha = np.clip(transported[:, :, 3:4], 0, 1)
        rgb = np.divide(transported[:, :, :3], np.maximum(alpha, .00001))
        return Image.fromarray(np.uint8(np.clip(np.concatenate([rgb,alpha],axis=2),0,1)*255))


class Insect:
    def __init__(self, image, axis, joint, body_radius, species, body_polygons=(), wing_polygons=(), wing_sides=None):
        self.image, self.species = image, species
        self.axis = np.asarray(axis,dtype=float); self.axis /= np.linalg.norm(self.axis)
        self.perpendicular = np.array([-self.axis[1],self.axis[0]])
        self.joint = np.asarray(joint,dtype=float)
        y,x = np.mgrid[:image.height,:image.width]
        dx,dy = x-joint[0],y-joint[1]
        across = dx*self.perpendicular[0] + dy*self.perpendicular[1]
        along = dx*self.axis[0] + dy*self.axis[1]
        body = np.abs(across)<body_radius
        body |= np.asarray(traced_mask(image.size,body_polygons,feather=0))>0
        alpha = np.asarray(image.getchannel('A'))
        self.body=image.copy();self.body.putalpha(Image.fromarray(np.uint8(alpha*body)))
        self.wings=[]
        covered=body.copy()
        if wing_polygons and len(wing_polygons)==1:
            specifications=[((wing_sides or [-1])[0],True)]
        else:
            specifications=[(side,fore) for side in [-1,1] for fore in ([True] if species=='butterfly' or len(wing_polygons)==2 else [True,False])]
        for side,fore in specifications:
            if wing_polygons:
                polygon=wing_polygons[len(self.wings)]
                mask=(~covered)&(np.asarray(traced_mask(image.size,[polygon],feather=0))>0)
            else:
                mask=(~body)&(across*side>0)&((along>=-2) if fore else (along<-2))
            covered|=mask
            part=image.copy();part.putalpha(Image.fromarray(np.uint8(alpha*mask)))
            hinge=self.joint + self.perpendicular*side*(body_radius*.55) + self.axis*(2 if fore else -2)
            self.wings.append((part,side,fore,hinge))
        missing=(alpha>0)&(~covered)
        if np.any(missing) and np.max(alpha[missing])<=20:
            # Source resampling leaves faint fringes outside the traced lobes.
            # Preserve each original fringe pixel on its nearest substantial
            # painted component; never hide a missed body or wing by this rule.
            components=[self.body]+[wing[0] for wing in self.wings]
            channels=[np.asarray(item.getchannel('A')).copy() for item in components]
            points=[np.column_stack(np.nonzero(channel>20)) for channel in channels]
            for py,px in zip(*np.nonzero(missing)):
                distances=[np.min(np.sum((points_for_component-[py,px])**2,axis=1)) for points_for_component in points]
                nearest=int(np.argmin(distances))
                channels[nearest][py,px]=alpha[py,px]
                covered[py,px]=True
            for item,channel in zip(components,channels):item.putalpha(Image.fromarray(channel))
        missing=(alpha>0)&(~covered)
        if np.any(missing):
            ys,xs=np.nonzero(missing)
            raise ValueError(f'Anatomical masks omit{len(xs)} painted pixels: {list(zip(xs.tolist(),ys.tolist(),alpha[ys,xs].tolist()))[:30]}')

    def frame(self,time):
        if time<=0:return self.image.copy()
        entry=float(smooth(time/.25))
        if self.species=='butterfly':
            # Limited wing-plane projection keeps body, head and antennae at
            # unit scale. No underside or change of view is fabricated.
            samples=[time]; frequency=3.1; maximum=52
            translation=(6.5*time*entry, (-4.5*time + 1.5*math.sin(1.8*time))*entry)
        else:
            # A fast wing stroke is integrated across the exposure. Readable
            # slow width-squashing is inappropriate for this tiny dragonfly.
            samples=[time+d for d in [-.014,-.007,0,.007,.014]]
            frequency=24.5; maximum=19
            translation=(5.5*time*entry, -1.0*time*entry)
        if hasattr(self,'velocity_override') and self.velocity_override is not None:
            translation=tuple(np.asarray(self.velocity_override)*time*entry)
        accumulated=np.zeros((self.image.height,self.image.width,4),dtype=np.float32)
        for t in samples:
            wings=Image.new('RGBA',self.image.size)
            for part,side,fore,hinge in self.wings:
                angle=maximum*(.5-.5*math.cos(math.tau*frequency*t + (0 if fore else .13)))*entry
                scale=math.cos(math.radians(angle*(1 if side<0 else .88)))
                matrix=np.outer(self.axis,self.axis) + scale*np.outer(self.perpendicular,self.perpendicular)
                matrix=rotation(side*angle*.11)@matrix
                wings.alpha_composite(affine(part,matrix,hinge))
            raw=np.asarray(wings).astype(np.float32)/255
            raw[:,:,:3]*=raw[:,:,3:4];accumulated+=raw/len(samples)
        alpha=accumulated[:,:,3:4]
        colors=np.divide(accumulated[:,:,:3],np.maximum(alpha,.00001))
        result=Image.fromarray(np.uint8(np.clip(np.concatenate([colors,alpha],axis=2),0,1)*255))
        result.alpha_composite(self.body)
        return affine(result,np.eye(2),(0,0),translation)


def traced_mask(size, polygons, exclusions=(), feather=2):
    """Hand-traced selection masks are geometry, never substitute painted art."""
    mask=Image.new('L',size);draw=ImageDraw.Draw(mask)
    for polygon in polygons:draw.polygon(polygon,fill=255)
    for polygon in exclusions:draw.polygon(polygon,fill=0)
    return mask.filter(ImageFilter.GaussianBlur(feather)) if feather else mask


class Pond:
    # Traced on the original 1280x1600 master. Banks, bridge, stones, lily beds
    # and the visible koi are excluded; only existing water pixels are moved.
    # Water interior only: uncertain shore silhouettes have a static safety
    # band. These points deliberately exclude banks instead of chasing every
    # leaf edge and risking material motion on solid objects.
    SURFACE=[(452,753),(810,749),(1020,793),(1020,884),(1052,914),
             (1045,955),(1010,1000),(1035,1050),(1020,1095),(906,1120),
             (888,1230),(804,1270),(789,1410),(760,1510),(720,1530),
             (650,1470),(515,1430),(477,1350),(425,1260),(405,1155),
             (371,1090),(380,1045),(560,1020),(590,980),(590,913),
             (550,880),(432,856)]
    EXCLUSIONS=[[(457,1380),(644,1388),(772,1430),(790,1528),(685,1560),(516,1510)],
                [(601,990),(808,981),(818,1048),(704,1080),(609,1061)],
                [(796,1047),(959,1018),(1001,1054),(919,1105),(811,1120)],
                [(302,1100),(531,1091),(590,1124),(606,1167),(506,1192),(331,1180)],
                [(360,1229),(565,1225),(689,1249),(709,1300),(621,1354),(436,1347)]]
    FALLS=[[(523,566),(561,566),(586,610),(574,625),(539,616)],
           [(515,619),(583,619),(605,704),(547,717),(522,697)]]

    def __init__(self,background):
        self.background=background.convert('RGB');self.raw=np.asarray(self.background).astype(np.float32)
        self.y,self.x=np.mgrid[:background.height,:background.width].astype(np.float32)
        sx,sy=background.width/1280,background.height/1600
        scale=lambda poly:[(round(x*sx),round(y*sy)) for x,y in poly]
        self.surface=traced_mask(background.size,[scale(self.SURFACE)],[scale(p) for p in self.EXCLUSIONS],3)
        self.falls=traced_mask(background.size,[scale(p) for p in self.FALLS],feather=2)
        self.surface_alpha=np.asarray(self.surface,dtype=np.float32)[:,:,None]/255
        self.fall_alpha=np.asarray(self.falls,dtype=np.float32)[:,:,None]/255

    def frame(self,time):
        # Water reflections are long horizontal structures. Travelling phases
        # move highlights laterally with perspective, not every scene object.
        depth=np.clip((self.y-605)/720,0,1)
        entry=float(smooth(time/.30))
        dx=(1.1+2.4*depth)*(np.sin(self.y*.092-time*3.9)+.32*np.sin(self.y*.177-time*5.5+self.x*.006))*entry
        dy=.45*depth*np.sin(self.y*.06-time*2.8+self.x*.003)*entry
        water=bilinear(self.raw,self.x+dx,self.y+dy)
        output=self.raw*(1-self.surface_alpha)+water*self.surface_alpha
        # Two staggered advection phases continuously send painted streaks
        # down each waterfall; blending hides texture wrap, not emission.
        period=19.; travel=time*47.; phase=(travel%period)/period
        a=bilinear(self.raw,self.x+.45*np.sin(self.y*.2-time*4),self.y-(travel%period))
        b=bilinear(self.raw,self.x,self.y-((travel+period*.5)%period))
        weight=.5-.5*math.cos(math.tau*phase)
        falls=(a*weight+b*(1-weight))*entry+self.raw*(1-entry)
        output=output*(1-self.fall_alpha)+falls*self.fall_alpha
        return Image.fromarray(np.uint8(np.clip(output,0,255))).convert('RGBA')


class StableFloat:
    """A solid leaf or lily moves as one rigid object on the water."""
    def __init__(self,image,phase=0):
        self.image=image;self.phase=phase
    def frame(self,time):
        if time<=0:return self.image.copy()
        # Offset subtraction starts on the exact original pose without an end reset.
        dx=1.6*(math.sin(time*.72+self.phase)-math.sin(self.phase))
        dy=.8*(math.sin(time*.93+self.phase)-math.sin(self.phase))
        angle=.20*(math.sin(time*.8+self.phase)-math.sin(self.phase))
        return affine(self.image,rotation(angle),(self.image.width*.5,self.image.height*.5),(dx,dy))


class RigidDrift:
    """Preserve the complete painted animal/cloud anatomy on a short glide."""
    def __init__(self,image,velocity):self.image=image;self.velocity=velocity
    def frame(self,time):
        if time<=0:return self.image.copy()
        entry=float(smooth(time/.30))
        return affine(self.image,np.eye(2),(0,0),np.asarray(self.velocity)*time*entry)


class SurfaceFlow:
    """Move painted light/reflection texture while holding its silhouette fixed."""
    def __init__(self,image,kind='water',phase=0):
        self.image=image;self.raw=np.asarray(image).astype(np.float32)/255
        self.y,self.x=np.mgrid[:image.height,:image.width].astype(np.float32)
        self.kind=kind;self.phase=phase
    def frame(self,time):
        if time<=0:return self.image.copy()
        entry=float(smooth(time/.30))
        premultiplied=self.raw.copy();premultiplied[:,:,:3]*=premultiplied[:,:,3:4]
        if self.kind=='flame':
            # Continuous local color advection within the source flame contour.
            # Its log attachment and alpha boundary never pulse or detach.
            period=max(8,self.image.height*.20);travel=time*28
            phase=(travel%period)/period;weight=.5-.5*math.cos(math.tau*phase)
            a=bilinear(premultiplied,self.x,self.y-(travel%period))
            b=bilinear(premultiplied,self.x,self.y-((travel+period*.5)%period))
            transported=a*weight+b*(1-weight)
            sampled=np.divide(transported[:,:,:3],np.maximum(transported[:,:,3:4],.00001))
            sampled=np.where(transported[:,:,3:4]>.01,sampled,self.raw[:,:,:3])
            rgb=self.raw[:,:,:3]*(1-entry)+sampled*entry
        else:
            dx=1.5*np.sin(self.y*.09-time*3.9+self.phase)*entry
            dy=.22*np.sin(self.y*.06-time*2.8+self.phase)*entry
            sampled=bilinear(premultiplied,self.x+dx,self.y+dy)
            rgb=np.divide(sampled[:,:,:3],np.maximum(sampled[:,:,3:4],.00001))
            rgb=np.where(sampled[:,:,3:4]>.01,rgb,self.raw[:,:,:3])
        # Alpha is an inspected fixed material boundary, not a moving sheet.
        result=Image.fromarray(np.uint8(np.round(np.clip(np.dstack([rgb,self.raw[:,:,3]]),0,1)*255)))
        result.putalpha(self.image.getchannel('A'))
        return result


class ChimneySmoke(Steam):
    """Dense directional exhaust, transported away from the fixed chimney."""
    def frame(self,time):
        if time<=0:return self.image.copy()
        above=(self.height-1-self.y)/max(1,self.height-1)
        # The painted plume trails upper-left of its lower-right outlet.
        # Transport follows that direction; density is not a cup-wisp scale/fade.
        source_y=self.y+time*42
        source_x=self.x+time*15*above+2.0*above*np.sin(self.y*.07-time*1.1)
        first=bilinear(self.raw,source_x,source_y,wrap_y=True)
        second=bilinear(self.raw,source_x+3*above,source_y+self.height*.36,wrap_y=True)
        transported=first*.92+second*.16
        steady=smooth((above-.035)/.19)[...,None]
        transported=self.raw*(1-steady)+transported*steady
        transported*=smooth(self.y/max(1,self.height*.22))[...,None]
        entry=float(smooth(time/.35));transported=self.raw*(1-entry)+transported*entry
        alpha=np.clip(transported[:,:,3:4],0,1)
        rgb=np.divide(transported[:,:,:3],np.maximum(alpha,.00001))
        return Image.fromarray(np.uint8(np.round(np.clip(np.concatenate([rgb,alpha],axis=2),0,1)*255)))
