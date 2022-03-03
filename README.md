![collage_maker](https://user-images.githubusercontent.com/38915815/156572491-5004f58b-4c68-4b2c-9f0b-6fa0f91a72ac.PNG)

# Collage-Creator ✏️
A simple app to create collages with your favourite images! You can drag and drop, scale and crop, and apply filters to the images. Give it a go! 🙌

This project was built as a class project for my grade 12 computer science course. I spent more time making this than I'd like to admit. My teacher went so far as to say, "But why...?".

# Steps for Building

This project uses the visual studio compiler, so you will need to install <a href="https://visualstudio.microsoft.com/vs/">Visual Studio</a> if you haven't already. At the time of writing, the latest version is 2019, so I cannot guarentee proper building for any subsequent versions. Also note that if your visual studio version is different than 2019, you will need to change *shell.bat* accordingly.   

After installing visual studio, clone this project and run the following commands. This will set up the visual studio compiler for use on the command line via the "cl" command. The *build.bat* script compiles the C platform layer and loads the python app into the build directory.

```
$ shell.bat
$ build.bat
```

To run the project, run the following commands

```
$ cd bin
$ Collage.exe
```

# Tech Used

The app runs as a python script loaded by a custom platform layer written in C. The platform layer runs the app via the <a href="https://docs.python.org/3/c-api/index.html">Python/C API</a>. The python scripts makes use of the <a href="https://pillow.readthedocs.io/en/stable/index.html">Python Imaging Library</a>.

# Documentation

It is possible to reuse the custom platform layer to create novel apps. I have provided documentation in the form of a wiki under this repo. Head <a href="https://github.com/BluBloos/collage-creator/wiki/Docs">here</a>.
