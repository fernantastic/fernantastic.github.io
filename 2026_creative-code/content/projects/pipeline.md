+++
draft = false
title = "Case Study: A Stylized Art Pipeline for Unity"
home_img = "projects/pipeline/cameras/Main_Camera__Corner_Colorful.asset.jpg"
home_title = "Case Study: A Stylized Art Pipeline for Unity"
home_subtitle = "Unity Editor Extensions, Shaders, Art Pipeline"
description = "I designed and implemented an artist-friendly stylized art pipeline with custom lighting and interchangeable palette assets."
side = """
Skills:
Unity Editor Extensions
Technical Art
Codex
"""
+++

<!--{{< video "projects/pipeline/editing_shader.mp4" >}}-->

<!--{{< video "projects/pipeline/choosing_palettes.mp4" >}}-->

<!--{{< palette-comparison >}}-->


As part of a tech art test, I implemented an art pipeline that includes:

- An asset importer and processor that applies shaders and metadata to 3D Models
- A custom ubershader with a full custom recoloring, fog, lighting solution
- Editor tools for assigning color palettes to models interactively
- A color palette system with interchangeable palette assets for different looks
- No need for custom materials. A single drawcall renders the entire scene.


### tl;dr

1. Drag a model to the project, a custom importer applies the custom pipeline automatically.
2. Use an in-editor tool to assign palette indices to meshes. 
3. Create Palette assets for specific looks. 
4. No need for multiple materials: an ubershader handles the entire look. The entire shading is artist controlled.

### More information

 - [Full write-up and documentation about the process  at Notion](https://app.notion.com/p/Fernando-Ramallo-Technical-Art-Case-Study-A-stylized-Art-Pipeline-39d985971dce80da932ef7ef8aaebf68?source=copy_link)
 - [Full source code available on Github](https://github.com/fernantastic/unity-palette-pipeline)



#### Cycling through Palette objects
{{< img "projects/pipeline/choosing.gif" "" >}}


#### Editing a Palette’s shader lighting

{{< img "projects/pipeline/shader.gif" "" >}}

#### Editing a Palette

{{< img "projects/pipeline/tweaking.gif" "" >}}

#### Uber shader

{{< img "projects/pipeline/shader.png" "" >}}

## Screenshots

{{< img "projects/pipeline/cameras/Main_Camera__Corner_Colorful.asset.jpg" "Main Camera - Colorful" >}}
{{< img "projects/pipeline/cameras/Main_Camera__Corner_Desert.asset.jpg" "Main Camera - Desert" >}}
{{< img "projects/pipeline/cameras/Main_Camera__Corner_Night_1.asset.jpg" "Main Camera - Night" >}}
{{< img "projects/pipeline/cameras/Main_Camera_%282%29__Corner_Night.asset.jpg" "Main Camera (2) - Corner Night" >}}
{{< img "projects/pipeline/cameras/Main_Camera_%282%29__Corner_Night_1.asset.jpg" "Main Camera (2) - Corner Night variant" >}}
{{< img "projects/pipeline/cameras/Main_Camera_%282%29__Game_DebugPalette.asset.jpg" "Main Camera (2) - Debug Palette" >}}
{{< img "projects/pipeline/cameras/Main_Camera_%283%29__Corner_Desert.asset.jpg" "Main Camera (3) - Desert" >}}
{{< img "projects/pipeline/cameras/Main_Camera_%283%29__Corner_Empty.asset.jpg" "Main Camera (3) - Empty" >}}
{{< img "projects/pipeline/cameras/Main_Camera_%283%29__Corner_Night_1.asset.jpg" "Main Camera (3) - Night" >}}
{{< img "projects/pipeline/cameras/Main_Camera_%286%29__Corner_Foggy.asset.jpg" "Main Camera (6) - Foggy" >}}
{{< img "projects/pipeline/cameras/Main_Camera_%286%29__Corner_Night.asset.jpg" "Main Camera (6) - Night" >}}
{{< img "projects/pipeline/cameras/Main_Camera_%286%29__Corner_Night_1.asset.jpg" "Main Camera (6) - Night variant" >}}


## See more

 - [Full write-up and documentation about the process  at Notion](https://app.notion.com/p/Fernando-Ramallo-Technical-Art-Case-Study-A-stylized-Art-Pipeline-39d985971dce80da932ef7ef8aaebf68?source=copy_link)
 - [Full source code available on Github](https://github.com/fernantastic/unity-palette-pipeline)
