from audioop import bias
from doctest import NORMALIZE_WHITESPACE
from math import pi, sqrt, tan
from numpy import exp2
import pygame
import pygame.gfxdraw
import pygame.math
from pygame.color import Color
from pygame.math import Vector3

MAX_RAY_DEPTH = 4
BIAS = 1e-4

class Sphere:
    center : Vector3
    radius : float
    color : Color
    def __init__(self, _center, _radius, _color):
        self.center = _center
        self.radius = _radius
        self.color = _color

class Ray:
    origin : Vector3
    direction : Vector3
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction

def mix(x, y, a):
    return x * (1 - a) + y * a

def mulColors(x : Color, y : Color, ignorealpha = True) -> Color:
    z = Color(255,255,255,255)
    if ignorealpha:
        z.r = x.r * y.r if x.r * y.r < 255 else 255
        z.g = x.g * y.g if x.g * y.g < 255 else 255
        z.b = x.b * y.b if x.b * y.b < 255 else 255
    else:
        z.a = x.a * y.a if x.a * y.a < 255 else 255
    
    return z

def mulColor(x : Color, a : float) -> Color:
    c = Color(x.r * a, x.g * a, x.b * a)
    return c
    

# Be sure to provide the unit vector first
def project(vec1 : Vector3, vec2 : Vector3):
    vu = Vector3.dot(vec1, vec2)
    v1l = vec1.length()
    if v1l < 1 or v1l > 1:
        vu = vu / v1l

    return vec1 * vu

def sphere_intersect(ray : Ray, sphere : Sphere):
    l = sphere.center - ray.origin
    tca = l.dot(ray.direction)
    if tca < 0: return False, 0, 0
    d2 = l.dot(l) - tca * tca
    if d2 > sphere.radius * sphere.radius: return False, 0, 0
    thc = sqrt(sphere.radius * sphere.radius - d2)
    t0 = tca - thc
    t1 = tca + thc

    return True, t0, t1

def trace(ray : Ray, spheres : set, depth = 0) -> Color:
    tnear = float('inf')
    lastsphere : Sphere = None
    surfaceColor = Color(0,0,0,0)

    for sphere in spheres:
        t0 = float('inf')
        t1 = float('inf')
        inter, t0, t1 = sphere_intersect(ray, sphere)
        if inter:
            if t0 < 0: t0 = t1
            if t0 < tnear:
                tnear = t0
                lastsphere = sphere
    
    if lastsphere == None:
        return Color(0,0,0)
    
    inside, phit, nhit = get_hit(ray, lastsphere, tnear)

    if depth < MAX_RAY_DEPTH:
        facingratio = -ray.direction.dot(nhit)
        fresneleffect = max(0, mix(pow(1 - facingratio, 3), 1, 0.1))

        refldir = ray.direction - nhit * 2 * ray.direction.dot(nhit)
        refldir.normalize()
        reflray = Ray(phit + nhit * BIAS, refldir)
        reflection = trace(reflray, spheres, depth + 1)
        fresnelr = reflection.r * fresneleffect
        fresnelg = reflection.g * fresneleffect
        fresnelb = reflection.b * fresneleffect
        r = Color(int(fresnelr), int(fresnelg), int(fresnelb))
        #surfaceColor = mulColors(mulColors(reflection, lastsphere.color), r)
        surfaceColor = r.lerp(lastsphere.color, 0.5)
    

    return lastsphere.color + surfaceColor


def get_hit(ray : Ray, sphere : Sphere, tnear : float):
    phit = ray.origin + ray.direction * tnear
    nhit = phit - sphere.center
    nhit.normalize()
    inside = False
    if ray.direction.dot(nhit) > 0: 
        nhit = -nhit
        inside = True

    return inside, phit, nhit

def sphereIntersect(p : Vector3, d : Vector3, c : Vector3, r : float):
    vpc = c - p
    if vpc.dot(d) < 0: # Sphere center behind the ray's origin

        if vpc.length() > r: # Sphere behind ray
            return False
        
        else: # Ray is inside the sphere
            # pc = project(p + d, c)
            # pcc = (pc - c).length()
            # dist = sqrt(exp2(r) - pcc * pcc)
            # di1 = dist - (pc - p).length()
            # intersection = p + d * di1
            return True
    
    else: # Sphere center projects on the ray
        pc = project(p + d, c)
    
        if (c - pc).length() > r:
            return False
        else:
            return True


spheres = [
    Sphere(Vector3(0, 2, -4), 1, Color(255,50,50)),
    Sphere(Vector3(3, 2, -6), 2, Color(50,255,50))
]

def main():
    pygame.init()
    width = 150
    height = 150
    screen = pygame.display.set_mode((width, height))
    screen.fill((255, 255, 255))
    s = pygame.Surface(screen.get_size(), pygame.SRCALPHA, 32)
    refls = pygame.Surface(screen.get_size(), pygame.SRCALPHA, 32)

    spherePos = Vector3(0, 2, -4)
    cameraPos = Vector3(0,0,0)
    cameraDir = Vector3(1,0,0)

    # Draw here
    invWidth = 1 / width
    invHeight = 1 / height
    fov = 60
    aspectRatio = width / height
    angle = tan(pi * 0.5 * fov / 180)
    
    try:
        while True:
            screen.fill((255,255,255))
            s.fill((255,255,255))
            refls.fill((255,255,255,0))
    
            for y in range(height):
                for x in range(width):
                    xx = (2 * ((x + 0.5) * invWidth) - 1) * angle * aspectRatio
                    yy = (1 - 2 * ((y + 0.5) * invHeight) * angle)
                    raydir = Vector3(xx, yy, -1) + cameraDir
                    raydir = raydir.normalize()

                    ray = Ray(cameraPos, raydir)

                    scolor = trace(ray, spheres)
                    pygame.gfxdraw.pixel(s, x, y, scolor)
                        
            
            screen.blit(s, (0, 0))
            screen.blit(refls, (0,0), pygame.Rect(0,0,refls.get_width(), refls.get_height()), pygame.BLEND_ALPHA_SDL2)

            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                cameraPos.y += 0.1
            if keys[pygame.K_s]:
                cameraPos.y -= 0.1
            if keys[pygame.K_a]:
                cameraPos.x -= 0.1
            if keys[pygame.K_d]:
                cameraPos.x += 0.1
            if keys[pygame.K_q]:
                cameraPos.z -= 0.1
            if keys[pygame.K_e]:
                cameraPos.z += 0.1

            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    break
                
            pygame.display.flip()
    finally:
        pygame.quit()




if __name__ == "__main__":
    main()