from hamamatsu.dcam import dcam

with dcam:
    with dcam[0] as cam:
        cam["exposure_time"] = 0.04
        print("exposure_time now:", cam.get("exposure_time"))
        try:
            cam["binning"] = 4
        except Exception:
            cam["binning"] = "4x4"
        print("binning now:", cam.get("binning"))
