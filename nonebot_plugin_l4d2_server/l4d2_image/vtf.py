try:
    from PIL import Image
    from srctools.vtf import VTF, ImageFormats
    # from srctools.vtf import VTF, ImageFormats
    from typing import IO

    async def img_to_vtf(pic:Image,tag):
        vtf_file:IO[bytes]
        vtf_ = VTF(1024, 1024, fmt = ImageFormats.DXT5,thumb_fmt = ImageFormats.DXT1,version=(7,2))
        for i in range(1):
            if tag == '覆盖':
                img2 = Image.new('RGBA',(1024, 1024), (255, 255, 255,0))
                r, g, b, a = pic.split()
                img2.paste(pic,mask=a)
                pic = pic.resize((1024,1024))
                break
            elif tag == '填充':
                w, h = pic.size
                a = w if w >=h else h
                point = a/1024
                pic.resize
                break
            else:
                pic = pic.resize((1024,1024))
        largest_frame = vtf_.get()  # This retrieves the first frame with the largest mipmap size.
        # Copy into the frame, the format here is what PIL uses for non-transparent images. You'd want ImageFormats.RGBA8888 for transparent ones.
        largest_frame.copy_from(pic.tobytes(), ImageFormats.RGBA8888)
        vtf_.save(vtf_file)
except:
    pass