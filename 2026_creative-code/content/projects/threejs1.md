+++
draft = false
title = "Three.js experiments"
home_img = "projects/raymarching/vlcsnap-2026-01-26-16h59m06s373.jpg"
home_title = "Three.js experiments"
home_subtitle = "XR Prototyping, Unity"
side = """
Skills:
XR Development
Unity
"""
description = "!!"
+++


Examples of three.js work.

---

## Landscapse inside a fragment shader (Circular)
Using the webcam as an input texture to create a landscape inside a fragment shader.
* Move your hands over the webcam to change the shape of the landscapes

{{< threejsshader shader="landscapes1" tex1="webcam" tex2="webcam" mask="webcam" bloom="true" >}}

---
## Landscapse inside a fragment shader (Perspective)
Using the webcam as an input texture to create a landscape inside a fragment shader.
* Move your hands over the webcam to change the shape of the landscapes

{{< threejsshader shader="flying" tex1="webcam" tex2="noise1" mask="webcam" bloom="true" >}}
