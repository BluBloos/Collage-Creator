@echo off

del bin\app.py

pushd code
copy app.py ..\bin\
popd

pushd bin

cl -Zi -FeCollage -I ../lib ../code/Collage.cpp /link /LIBPATH:../lib -incremental:no user32.lib gdi32.lib Comdlg32.lib

popd
