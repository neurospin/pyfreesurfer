# tkmedit_slicer_edges.tcl


#-------------------------------------
# Load surfaces:
# 
#LoadMainSurface [0=main; 1=Aux] [filename] 

puts "Load main surfaces"
LoadMainSurface      0 lh.white
LoadPialSurface      0 lh.pial
LoadOriginalSurface  0 lh.orig

puts "Load aux surfaces"
LoadMainSurface      1 rh.white
LoadPialSurface      1 rh.pial
LoadOriginalSurface  1 rh.orig


#-------------------------------------
# Slice volume:

SetOrientation %(ORIENT)s
SetCursor 0 0 0 0
for { set slice %(START)s } { $slice <= %(END)s } { incr slice %(INCR)s } {
    SetSlice $slice
    RedrawScreen
    SaveRGB %(RGBFILE)s
}

UnloadSurface 0
UnloadSurface 1
QuitMedit
