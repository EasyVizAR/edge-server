import svgwrite
import math

if __name__ == '__main__':
    dwg = svgwrite.Drawing('svgwrite-example.svg', profile='tiny')

    rad = 100
    for i in range(8):
        print("{}, {}".format(math.cos(math.pi/4*i)*rad, math.sin(math.pi/4*i)*rad))
        dwg.add(dwg.line(start = (math.cos(math.pi/4*i)*rad, math.sin(math.pi/4*i)*rad),
                end = (math.cos(math.pi/4*(i+1))*rad, math.sin(math.pi/4*(i+1))*rad),
                stroke=svgwrite.rgb(0, 0, 255, '%')
            )
        )

    print(dwg.tostring())
    dwg.save()
