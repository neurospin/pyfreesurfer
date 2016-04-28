# tkmedit_slicer_labels.tcl


#-------------------------------------
# Load surfaces and colormap:

puts "Load segmentation volume and colormap"
LoadSegmentationVolume nu.mgz aparc+aseg.mgz %(LOOKUPTABLE)s


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
