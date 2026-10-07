"""Offline physical rigs that deform original painted pixels; no generated art."""
import math
from PIL import Image
from encode_scene import deform, fade, painted_action, smooth


def rig(cutout, profile, phase):
    if 'previewRecipePart' in profile:
        return painted_action(cutout,profile['previewRecipePart'],phase)
    pad=28;w,h=cutout.size
    im=Image.new('RGBA',(w+pad*2,h+pad*2));im.alpha_composite(cutout,(pad,pad))
    if phase<=0 or phase>=1:return im,(-pad,-pad)
    kind=profile['motion'];envelope=math.sin(math.pi*phase)**2
    phase_offset=profile.get('phaseOffset',0)
    a=profile['amplitudePt']*3
    pivot=(pad+profile['anchor'][0]*w,pad+profile['anchor'][1]*h)
    wave=math.sin(math.tau*phase+phase_offset)
    if kind=='steam':return painted_action(cutout,0,phase)
    if kind=='fabric_left':
        def flag(x,y):
            free=max(0,min(1,(x-pivot[0])/max(1,w*.95)))
            shift=a*envelope*math.sin(math.tau*phase+phase_offset-free*.7)*free**2
            return x,y-shift
        return deform(im,flag),(-pad,-pad)
    if kind in ['plant','fabric_top']:
        top=profile['anchorKind']=='top'; span=max(1,h*.95)
        def bend(x,y):
            free=max(0,min(1,(y-pivot[1] if top else pivot[1]-y)/span))
            delay=.65*free if kind=='fabric_top' else 0
            shift=a*envelope*math.sin(math.tau*phase+phase_offset-delay)*free**2
            return x-shift,y-abs(shift)*.12*free
        return deform(im,bend),(-pad,-pad)
    if kind in ['fabric_join','leaf_join']:
        radius=max(w,h)*.55
        def flutter(x,y):
            dx,dy=x-pivot[0],y-pivot[1];r=min(1,math.hypot(dx,dy)/radius)**2
            angle=math.atan2(dy,dx);amount=a*.65*envelope*math.sin(4*math.pi*phase+angle*2+phase_offset)*r
            return x+math.sin(angle)*amount,y-math.cos(angle)*amount
        return deform(im,flutter,8),(-pad,-pad)
    if kind in ['pendulum','kite','resting']:
        if kind=='resting':pivot=(pad+w*.5,pad+h*.9)
        angle=min(.065,a/max(w,h)) * envelope*wave
        if kind=='resting':angle*=.4
        cosine,sine=math.cos(angle),math.sin(angle)
        def rotate(x,y):
            dx,dy=x-pivot[0],y-pivot[1]
            return pivot[0]+cosine*dx+sine*dy,pivot[1]-sine*dx+cosine*dy
        dx=round(a*.45*math.sin(math.pi*phase)*wave) if kind=='kite' else 0
        return deform(im,rotate),(-pad+dx,-pad)
    if kind=='garland':
        def hang(x,y):
            free=math.sin(math.pi*max(0,min(1,(x-pad)/w)))**2
            return x,y-a*.7*envelope*wave*free
        return deform(im,hang),(-pad,-pad)
    if kind in ['butterfly','bee','dragonfly','bird']:
        joint=(pad+profile['bodyJoint'][0]*w,pad+profile['bodyJoint'][1]*h)
        ax,ay=profile['bodyAxis'];length=math.hypot(ax,ay);ax/=length;ay/=length;px,py=-ay,ax
        cycles={'butterfly':8,'bee':15,'dragonfly':12,'bird':3}[kind]
        contraction={'butterfly':.52,'bee':.32,'dragonfly':.27,'bird':.28}[kind]
        flap=(.5-.5*math.cos(math.tau*cycles*phase))*envelope
        radius=max(w,h)*({'bird':.09,'bee':.12}.get(kind,.035))
        def wings(x,y):
            dx,dy=x-joint[0],y-joint[1];along=dx*ax+dy*ay;across=dx*px+dy*py
            if abs(across)>radius:
                scale=1-contraction*flap*(1 if across<0 else .82)
                across=math.copysign(radius+(abs(across)-radius)/scale,across)
            return joint[0]+along*ax+across*px,joint[1]+along*ay+across*py
        dx=round(a*.50*math.sin(math.tau*phase)*math.sin(math.pi*phase));dy=round(-a*.70*envelope)
        return deform(im,wings,5),(-pad+dx,-pad+dy)
    if kind=='perched_bird':
        def nod(x,y):
            localx=(x-pad)/w;localy=(y-pad)/h
            head=smooth((localx-.46)/.4)*(1-smooth((localy-.40)/.35))
            tail=(1-smooth((localx-.05)/.45))*smooth((localy-.20)/.4)*(1-smooth((localy-.75)/.15))
            dy=a*.45*envelope*(wave*head+math.sin(4*math.pi*phase)*tail)
            return x,y-dy
        return deform(im,nod,8),(-pad,-pad)
    if kind=='crawl':
        def steps(x,y):
            rx=(x-pad-w*.5)/(w*.5);ry=(y-pad-h*.5)/(h*.5)
            limbs=max(0,min(1,(math.hypot(rx,ry)-.45)/.55))
            stride=a*.30*envelope*math.sin(10*math.pi*phase+rx*2)*limbs
            return x-stride,y-stride*.35
        return deform(im,steps,7),(-pad+round(a*.55*envelope*wave),-pad)
    if kind in ['water','float','cloud','flame']:
        def flow(x,y):
            nx=(x-pad)/w;ny=(y-pad)/h
            if kind=='flame':
                free=max(0,min(1,1-ny))**2
                return x-a*.4*envelope*math.sin(6*math.pi*phase+ny*2)*free,y+a*.7*envelope*(.5+.5*math.sin(4*math.pi*phase))*free
            amplitude=a*(.28 if kind=='water' else .18)
            return x-amplitude*envelope*math.sin(math.tau*phase+ny*4),y-amplitude*.4*envelope*math.sin(math.tau*phase+nx*3)
        result=deform(im,flow,8)
        if kind=='water':result=fade(result,1-.16*envelope*(.5+.5*math.sin(4*math.pi*phase)))
        if kind=='cloud':return result,(-pad+round(a*.6*envelope*wave),-pad)
        if kind=='float':return result,(-pad+round(a*.3*envelope*wave),-pad+round(a*.35*envelope*math.sin(2*math.pi*phase)))
        return result,(-pad,-pad)
    raise ValueError('Unreviewed physical rig: '+kind)
