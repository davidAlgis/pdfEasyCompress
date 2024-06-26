import argparse
from pypdf import PdfReader, PdfWriter
from PIL import Image
import io
import tqdm
import os

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def create_minimal_white_image():
    return Image.new('RGB', (1, 1), color='white')

def parse_page_numbers(pages_string):
    if not pages_string:
        return None
    pages = set()
    for part in pages_string.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    return pages

def compress_image(image, quality=80, convert_png=True):
    if not isinstance(image, Image.Image):
        image = Image.open(io.BytesIO(image))
    
    img_format = image.format.lower() if image.format else 'jpeg'
    
    if img_format == 'jpeg' or (img_format == 'png' and convert_png):
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            # If the PNG has an alpha channel, blend it with a white background
            background = Image.new('RGBA', image.size, (255, 255, 255))
            image = Image.alpha_composite(background, image.convert('RGBA')).convert('RGB')
        
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        return Image.open(output)
    else:
        return image  # Return the original image if it's not JPEG or PNG

parser = argparse.ArgumentParser(description="Reduce the size of images in a PDF file")
parser.add_argument('-i', '--input', type=str, required=True, help='The PDF file to process')
parser.add_argument('-o', '--output', type=str, default=None, help='The name of the output PDF file')
parser.add_argument('-q', '--quality', type=int, default=80, help='The quality of the JPEG images (default: 80)')
parser.add_argument("-l", "--lossless", type=str2bool, nargs='?', const=True, default=False,
                    help="Indicate if compression should be lossless (default is false)")
parser.add_argument("-ri", "--removeImages", type=str2bool, nargs='?', const=True, default=False,
                    help="Replace all images with a minimal white image (default: false)")
parser.add_argument("-sp", "--selectPages", type=str, default="",
                    help="Comma-separated list of page numbers or ranges to keep (e.g., '1,3-5,7'). If not specified, all pages are kept.")
parser.add_argument("-cp", "--convertPNG", type=str2bool, nargs='?', const=True, default=True,
                    help="Convert PNG images to JPEG (default: true)")

args = parser.parse_args()

if args.output is None:
    args.output = os.path.splitext(args.input)[0] + "_compressed.pdf"

pages_to_keep = parse_page_numbers(args.selectPages)

try:
    reader = PdfReader(args.input)
except FileNotFoundError:
    print(f"Error: The file '{args.input}' was not found.")
    exit(1)

writer = PdfWriter()
minimal_white_image = create_minimal_white_image()

print("Processing pages...")
for i, page in enumerate(tqdm.tqdm(reader.pages, desc="Processing pages"), start=1):
    if pages_to_keep is None or i in pages_to_keep:
        writer_page = writer.add_page(page)
        
        if args.removeImages:
            for img in writer_page.images:
                img.replace(minimal_white_image)
        elif not args.lossless:
            for img in writer_page.images:
                compressed_image = compress_image(img.image, quality=args.quality, convert_png=args.convertPNG)
                img.replace(compressed_image)
        
        if args.lossless:
            writer_page.compress_content_streams()

try:
    with open(args.output, "wb") as f:
        writer.write(f)
except Exception as e:
    print(f"Error: Failed to save the result. {e}")
    exit(1)

print(f"Done. The result is saved at {args.output}")

input_size = os.path.getsize(args.input) / (1024 * 1024)
output_size = os.path.getsize(args.output) / (1024 * 1024)
size_reduction = (input_size - output_size) / input_size * 100
print(f"The output file size is {output_size:.2f} MiB which gave us a size reduction of {size_reduction:.2f}%.")