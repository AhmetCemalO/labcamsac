from pyDCAM import dcamapi_init, dcamapi_uninit, HDCAM
from pyDCAM.dcamapi_enum import DCAM_IDSTR

n = dcamapi_init()
print("cams:", n)
for i in range(n):
    with HDCAM(i) as cam:
        print(i, cam.dcamdev_getstring(DCAM_IDSTR.DCAM_IDSTR_CAMERAID))
dcamapi_uninit()
