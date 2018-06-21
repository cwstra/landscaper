import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageMath 
import ujson as json

with open('settings.json') as data_file:
    settings = json.load(data_file)

print(settings['color_array'])
print(settings['height_array'])

print("Turning image into array")

oImg = Image.open(settings['heightmap_name'])
heightImg = ImageMath.eval('im/256', {'im':oImg}).convert('L')
heightArr = np.array(heightImg)

def heightfunction(ele):
    def f(height):
        try:
            under = next(i for i,j in enumerate(settings['height_array']) if j>= height)
            return settings['color_array'][under][ele]
        except StopIteration:
            return settings['color_array'][-1][ele]
    return np.vectorize(f,['uint8'])

print('Colorifying')

colorArr = np.stack([heightfunction(0)(heightArr),heightfunction(1)(heightArr),heightfunction(2)(heightArr)],2)
colorImg = Image.fromarray(colorArr)
colorImg = colorImg.convert('RGBA')
colorImg.show()
print('Filtering maps')

def filterImg(img, ele):
    data = np.array(img)
    data[(data != (ele[0], ele[1], ele[2], 255)).any(axis = -1)] = (0,0,0,0) 
    return Image.fromarray(data, mode='RGBA')

landImg = Image.new('RGBA', colorImg.size, (0,0,0,0))
singleImgs = []
for ind, data in enumerate(settings['color_array']):
    sing = filterImg(colorImg, data)
    sing.show()
    if ind <= 2:
        singleImgs.append(sing)
    else:
        landImg.paste(sing, None, sing)

#for i in singleImgs:
#   i.show()
#landImg.show()
#colorImg.show()

print('Painting coastlines')

def blobmake(blobrad, color):
    blobsize = blobrad * 2 - 1 
    blob = Image.new('RGBA', (blobsize, blobsize), (0,0,0,0))
    brush = ImageDraw.Draw(blob)
    brush.ellipse([(0,0), (blobsize, blobsize)], tuple(color))
    return blob
shoreblob = blobmake(settings['shore_blob'], settings['color_array'][6])
shoalblob = blobmake(settings['shoal_blob'], settings['color_array'][0])
coastblob = blobmake(settings['coast_blob'], settings['color_array'][1])

shoretrace = Image.new('RGBA', colorImg.size, (0,0,0,0))
shoaltrace = Image.new('RGBA', colorImg.size, (0,0,0,0))
coasttrace = Image.new('RGBA', colorImg.size, (0,0,0,0))
flatimage = colorImg.getdata()
rowsize = colorImg.size[0]
seacolors = settings['color_array'][:3]

for ind, pix in enumerate(flatimage):
    if [pix[0],pix[1],pix[2]] in seacolors:
        shoretrace.paste(shoreblob, tuple(np.subtract(divmod(ind, rowsize)[::-1], (settings['shore_blob'], settings['shore_blob']))), shoreblob)
    else:
        shoaltrace.paste(shoalblob, tuple(np.subtract(divmod(ind, rowsize)[::-1], (settings['shoal_blob'], settings['shoal_blob']))), shoalblob)
        coasttrace.paste(coastblob, tuple(np.subtract(divmod(ind, rowsize)[::-1], (settings['coast_blob'], settings['coast_blob']))), coastblob)

black = Image.new('L', colorImg.size, 0)
shoremask = Image.new('L', colorImg.size, 255)
black.paste(shoremask, None, shoretrace)
shoremask = black
black = Image.new('L', colorImg.size, 0)
black.paste(shoremask, None, landImg)
shoremask = black

shoretrace.show()
landImg.show()

print("Finishing Up")

endImg = Image.new('RGBA', colorImg.size, (0,0,0,0))
endImg.paste(singleImgs[2],None,singleImgs[2])
endImg.paste(singleImgs[1],None,singleImgs[1]);endImg.paste(coasttrace,None,coasttrace)
endImg.paste(singleImgs[0],None,singleImgs[0]);endImg.paste(shoaltrace,None,shoaltrace)
endImg.paste(landImg,None,landImg)
endImg.paste(shoretrace, None, shoremask)


endImg.convert('RGB').save('out.png','png')

