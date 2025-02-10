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
            background = Image.new('RGBA', image.size, (255, 255, 255))
            image = Image.alpha_composite(background, image.convert('RGBA')).convert('RGB')
        
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        
        # Compare sizes
        compressed_size = output.tell()
        original_size = len(image.tobytes())

        if compressed_size >= original_size:
            return image  # Keep original if compressed size is larger
        
        return Image.open(output)
    else:
        return image  # Return original image if it's not JPEG or PNG

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
                original_image = img.image  
                compressed_image = compress_image(original_image, quality=args.quality, convert_png=args.convertPNG)
                
                # Compare sizes and replace only if compression is effective
                original_size = len(original_image.tobytes())
                compressed_size = len(compressed_image.tobytes())

                if compressed_size < original_size:
                    img.replace(compressed_image)
        
        if args.lossless:
            writer_page.compress_content_streams()

# Write compressed PDF to a temporary file
temp_output = args.output + ".temp"

try:
    with open(temp_output, "wb") as f:
        writer.write(f)
except Exception as e:
    print(f"Error: Failed to save the result. {e}")
    exit(1)

# Compare PDF sizes
input_size = os.path.getsize(args.input)
output_size = os.path.getsize(temp_output)

if output_size >= input_size:
    print(f"Warning: The compressed PDF ({output_size / (1024 * 1024):.2f} MiB) is larger than the original ({input_size / (1024 * 1024):.2f} MiB). Keeping the original file.")
    os.remove(temp_output)  # Remove the temporary file
    final_size = input_size
    final_path = args.input
else:
    # Fix: Remove existing file before renaming to avoid FileExistsError
    if os.path.exists(args.output):
        os.remove(args.output)
    os.rename(temp_output, args.output)
    
    final_size = output_size
    final_path = args.output

size_reduction = (input_size - final_size) / input_size * 100
print(f"Done. The result is saved at {final_path}")
print(f"The final file size is {final_size / (1024 * 1024):.2f} MiB, achieving a size reduction of {size_reduction:.2f}%.")
