"""
This is where we will store our ux related utilities, we do this so the stage systems don't need the additional graphical packages installed.
"""
from PIL import Image
from pathlib import Path
from colour import Color
from resizeimage import resizeimage
from warehouse.utils import file_exists, file_rename
from warehouse.math import percent_of


def to_color(limit_low, limit_high):
    """
    This converts a number into an RGB tuple this it defined within the limits
    """
    limit_high += 1
    blue = Color("blue")
    values = dict()
    colors = list(blue.range_to(Color("red"), abs(limit_high - limit_low)))
    labels = list(range(limit_low, limit_high))
    for idx, color in zip(labels, colors):
        values[idx] = Color.get_rgb(color)
    return values


def image_resize(x, y, image, x_percent, y_percent, preserve_aspect=True, folder_add=False, raw=False):
    """
    This resizes images to a percentage of x and y and saves it to the /img folder
    This skips the action if the resized file already exists.

    https://pypi.org/project/python-resize-image/
    https://unix.stackexchange.com/questions/75635/shell-command-to-get-pixel-size-of-an-image/235957
    libjpeg-turbo-devel

    TODO: We need to move the graphic support utilities into another module so stage isn't forced to use them.

    :param x: Layout x size in pixels.
    :type x: int
    :param y: Layout y size in pixels.
    :type y: int
    :param image: Filename of the base image.
    :type image: str
    :param x_percent: The x percentags of the output image.
    :type x_percent: int, float
    :param y_percent: The y percentage of the output image.
    :type y_percent: int, float
    :param preserve_aspect: Toggles preservation of the aspect ratio.
    :type preserve_aspect: bool
    :param folder_add: This adds a subfolder to the source path.
    :type folder_add: bool, str
    :param raw: Override folder locations.
    :type raw: bool

    :return: Resized image's file name.
    :rtype: str
    """
    ext = image.split('.')[1]
    base = Path.cwd()
    x_pix = percent_of(x, x_percent)
    y_pix = percent_of(y, y_percent)
    tp = base / Path('img/resize')

    tfn = tp / file_rename(str(x_pix) + '_' + str(y_pix), image)
    # print('target', tfn)
    if not file_exists(tfn) or raw:
        sp = base / Path('img/base')
        if folder_add:
            sp = base / Path('img/base/' + folder_add)
            if raw:
                sp = Path(folder_add)
                tfn = Path(image)

        sfn = sp / image
        # print('source', sfn)
        if file_exists(sfn):
            if ext == 'gif':  # Resize animated gif.
                resize_gif(sfn, tfn, (x_pix, y_pix))
            else:  # Resize still image.
                img = Image.open(sfn)
                if preserve_aspect:
                    img = resizeimage.resize_contain(img, [x_pix, y_pix])
                else:
                    img = resizeimage.resize_cover(img, [x_pix, y_pix], validate=False)
                img.save(tfn, img.format)
        else:
            print('target file not found:', tfn)
            raise FileNotFoundError
        print(sfn, tfn)
    return tfn.as_posix()


def resize_gif(path, save_as=None, resize_to=None, optimize=False):
    """
    Resizes the GIF to a given length:

    Args:
        path: the path to the GIF file
        save_as (optional): Path of the resized gif. If not set, the original gif will be overwritten.
        resize_to (optional): new size of the gif. Format: (int, int). If not set, the original GIF will be resized to
                              half of its size.
        optimize: Toggles frame optimizations.
    """
    all_frames = extract_and_resize_frames(path, resize_to)

    if not save_as:
        save_as = path

    if len(all_frames) == 1:
        print("Warning: only 1 frame found")
        all_frames[0].save(save_as, optimize=optimize)
    else:
        all_frames[0].save(save_as, optimize=optimize, save_all=True, append_images=all_frames[1:], loop=1000)


def analyseimage(path):
    """
    Pre-process pass over the image to determine the mode (full or additive).
    Necessary as assessing single frames isn't reliable. Need to know the mode
    before processing all frames.
    """
    im = Image.open(path)
    results = {
        'size': im.size,
        'mode': 'full',
    }
    try:
        while True:
            if im.tile:
                tile = im.tile[0]
                update_region = tile[1]
                update_region_dimensions = update_region[2:]
                if update_region_dimensions != im.size:
                    results['mode'] = 'partial'
                    break
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    return results


def extract_and_resize_frames(path, resize_to=None):
    """
    Iterate the GIF, extracting each frame and resizing them

    Returns:
        An array of all frames
    """
    mode = analyseimage(path)['mode']

    im = Image.open(path)

    if not resize_to:
        resize_to = (im.size[0] // 2, im.size[1] // 2)

    i = 0
    p = im.getpalette()
    last_frame = im.convert('RGBA')

    all_frames = []

    try:
        while True:
            # print("saving %s (%s) frame %d, %s %s" % (path, mode, i, im.size, im.tile))

            '''
            If the GIF uses local colour tables, each frame will have its own palette.
            If not, we need to apply the global palette to the new frame.
            '''
            if not im.getpalette():
                im.putpalette(p)

            new_frame = Image.new('RGBA', im.size)

            '''
            Is this file a "partial"-mode GIF where frames update a region of a different size to the entire image?
            If so, we need to construct the new frame by pasting it on top of the preceding frames.
            '''
            if mode == 'partial':
                new_frame.paste(last_frame)

            new_frame.paste(im, (0, 0), im.convert('RGBA'))

            new_frame.thumbnail(resize_to, Image.ANTIALIAS)
            all_frames.append(new_frame)

            i += 1
            last_frame = new_frame
            im.seek(im.tell() + 1)
    except EOFError:
        pass

    return all_frames
