
# Collage-Creator ✏️

> **Note to Reader:** This project was developed during my grade 12 year as part
> of a high school computer science course. This project does not reflect my
> current expertise.

A simple app to create collages with your favourite images! You can drag and
drop, scale and crop, and apply filters to the images. Give it a go! 🙌

![collage_maker](https://user-images.githubusercontent.com/38915815/156572491-5004f58b-4c68-4b2c-9f0b-6fa0f91a72ac.PNG)

# Tech Used

The app runs as a Python script loaded by a custom platform layer written in C.
The platform layer runs the app via the <a
href="https://docs.python.org/3/c-api/index.html">Python/C API</a>. The Python
scripts makes use of the <a
href="https://pillow.readthedocs.io/en/stable/index.html">Python Imaging
Library</a>.

# Features

- Native window menu:
    - Import image via native modal window.
    - Export the finished collage via a native modal window.
- Imported images are stored in an "image palette".
    - Drag an image to place on canvas.
- Canvas Interaction:
    - Drag images to translate on canvas.
    - Drag image edges to crop image (hold S to scale instead).
    - Images reside in layers.
- Visual effects:
    - Change cursor icons on mouse hover.
    - Animate application controls when hovered over.
- Image Context Menu (Right-click Menu):
    - Layer adjustments: "Bring to top", "Bring to bottom", "Step up", "Step down"
    - "Filter" (opens menu of filters to apply)
    - "Reset transform", "Reset filters"
    - "Remove" (removes image)
    - "Exit" (exits right-click menu)
- Program Context Menu (Right-click the canvas):
    - "Generate collage" (generates a random collage using the images in the palette)
    - "Go bannanas" (This is an easter egg - download the app to find out!)
- Apply multiple image filters as a set of transformations:
    - "Negate red" (negate the red channel)
    - "Negate red (banding)" (apply the filter but only in vertical bands)
    - "Monochrome"
    - "Radial vignette"
    - "Flip horizontal"
    - "Flip vertical"
    - "Gaussian blur"
    - "Emboss"
    - "Pixelate"
    - "Retro" (CRT effect)

# Steps for Building

This project uses the Visual Studio compiler; you will need to install <a
href="https://visualstudio.microsoft.com/vs/">Visual Studio</a> if you haven't
already. 

> At the time of writing, the latest version is 2019; I cannot guarantee
proper building for any subsequent versions. 

Note that if your Visual Studio version is different than 2019, you will need to
change *shell.bat*  
accordingly.

After installing Visual Studio, clone this project and run the following
commands. This will set up the Visual Studio compiler (MSVC) for use on the
command line via the "cl" command. The *build.bat* script compiles the C
platform layer and loads the Python app into the build directory.

```
$ shell.bat
$ build.bat
```

To run the project, run the following commands:

```
$ cd bin
$ Collage.exe
```
